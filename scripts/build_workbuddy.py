#!/usr/bin/env python3
"""Build a self-contained WorkBuddy skill-only Connector ZIP."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Any

try:
    from validate_skill import (
        ValidationFailure,
        compact_text,
        split_frontmatter,
        validate_workbuddy_package,
        validate_workbuddy_source,
    )
except ImportError as exc:
    print(
        "ERROR: scripts/validate_skill.py must be present next to this builder",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc


RESOURCE_DIRS = ("assets", "cases", "references", "scripts", "skills")
RESOURCE_FILES = ("kit.yaml",)
SKIP_DIRS = {".git", "dist", ".venv", "venv", "node_modules", "__pycache__"}
SKIP_FILES = {
    ".DS_Store",
    "build_workbuddy.py",
    "validate_skill.py",
}
SKIP_SUFFIXES = {".pyc", ".pyo"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="Skill source repository (default: current directory)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="New staging directory to create",
    )
    parser.add_argument(
        "--zip-path",
        type=Path,
        help="ZIP destination (default: OUTPUT_DIR.zip)",
    )
    parser.add_argument(
        "--individual-dir",
        type=Path,
        help="Directory for independently installable Skill ZIPs",
    )
    return parser.parse_args()


def fail_on_errors(errors: list[str], label: str) -> None:
    if errors:
        raise ValueError(f"{label} failed:\n- " + "\n- ".join(errors))


def ignore_resources(_directory: str, names: list[str]) -> set[str]:
    ignored = set()
    for name in names:
        path = Path(name)
        if (
            name in SKIP_DIRS
            or name in SKIP_FILES
            or path.suffix.lower() in SKIP_SUFFIXES
        ):
            ignored.add(name)
    return ignored


def copy_source_resources(source: Path, target: Path) -> None:
    shutil.copy2(source / "SKILL.md", target / "SKILL.md")
    for filename in RESOURCE_FILES:
        candidate = source / filename
        if candidate.is_file():
            shutil.copy2(candidate, target / filename)
    for dirname in RESOURCE_DIRS:
        candidate = source / dirname
        if candidate.is_dir():
            shutil.copytree(
                candidate,
                target / dirname,
                ignore=ignore_resources,
            )


def workbuddy_frontmatter(
    source_skill: Path, connector: dict[str, Any]
) -> tuple[str, str]:
    data, body = split_frontmatter(source_skill)
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        raise ValidationFailure(f"{source_skill}: metadata must be a mapping")
    fields: list[tuple[str, str]] = [
        ("name", compact_text(data.get("name"))),
        ("description", compact_text(data.get("description"))),
        ("version", compact_text(metadata.get("version"))),
        ("author", compact_text(metadata.get("author"))),
        ("source_type", compact_text(connector.get("source_type"))),
    ]
    for locator in ("clawhub_slug", "skillhub_slug", "git_url"):
        value = compact_text(connector.get(locator))
        if value:
            fields.append((locator, value))
    lines = ["---"]
    for key, value in fields:
        lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    lines.extend(("---", ""))
    return "\n".join(lines), body


def transform_skills(target: Path, connector: dict[str, Any]) -> None:
    for skill_file in sorted(target.rglob("SKILL.md")):
        frontmatter, body = workbuddy_frontmatter(skill_file, connector)
        skill_file.write_text(frontmatter + body, encoding="utf-8")


def write_zip(output_dir: Path, zip_path: Path) -> None:
    if zip_path.exists():
        raise FileExistsError(f"ZIP already exists: {zip_path}")
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(output_dir.rglob("*")):
            if path.is_file():
                archive.write(
                    path,
                    Path(output_dir.name) / path.relative_to(output_dir),
                )


def write_individual_zips(skills_dir: Path, individual_dir: Path) -> None:
    if individual_dir.exists():
        raise FileExistsError(
            f"individual ZIP directory already exists: {individual_dir}"
        )
    individual_dir.mkdir(parents=True)
    for skill_dir in sorted(skills_dir.iterdir()):
        if not (skill_dir / "SKILL.md").is_file():
            continue
        zip_path = individual_dir / f"{skill_dir.name}.zip"
        with zipfile.ZipFile(
            zip_path, "w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            for path in sorted(skill_dir.rglob("*")):
                if path.is_file():
                    archive.write(
                        path,
                        Path(skill_dir.name) / path.relative_to(skill_dir),
                    )


def build(
    source: Path,
    output_dir: Path,
    zip_path: Path,
    individual_dir: Path,
) -> None:
    source_errors: list[str] = []
    validate_workbuddy_source(source, source_errors)
    fail_on_errors(source_errors, "WorkBuddy source validation")

    if output_dir.exists():
        raise FileExistsError(f"output directory already exists: {output_dir}")
    if zip_path.exists():
        raise FileExistsError(f"ZIP already exists: {zip_path}")
    if individual_dir.exists():
        raise FileExistsError(
            f"individual ZIP directory already exists: {individual_dir}"
        )

    connector_path = source / "workbuddy" / "connector-meta.json"
    connector = json.loads(connector_path.read_text(encoding="utf-8"))
    source_data, _ = split_frontmatter(source / "SKILL.md")
    root_skill_name = compact_text(source_data.get("name"))

    output_dir.mkdir(parents=True)
    shutil.copy2(connector_path, output_dir / "connector-meta.json")
    icon = next(
        (
            candidate
            for candidate in (
                source / "workbuddy" / "icon.svg",
                source / "workbuddy" / "icon.png",
                source / "workbuddy" / "icon.jpg",
                source / "workbuddy" / "icon.jpeg",
            )
            if candidate.is_file()
        )
    )
    shutil.copy2(icon, output_dir / icon.name)

    skills_target = output_dir / "skills"
    skill_target = skills_target / root_skill_name
    skill_target.mkdir(parents=True)
    copy_source_resources(source, skill_target)

    source_modules = source / "skills"
    if source_modules.is_dir():
        for module_source in sorted(source_modules.iterdir()):
            module_skill = module_source / "SKILL.md"
            if not module_skill.is_file():
                continue
            module_data, _ = split_frontmatter(module_skill)
            module_name = compact_text(module_data.get("name"))
            module_target = skills_target / module_name
            module_target.mkdir(parents=True)
            copy_source_resources(module_source, module_target)

    transform_skills(skills_target, connector)

    package_errors: list[str] = []
    validate_workbuddy_package(output_dir, package_errors)
    fail_on_errors(package_errors, "WorkBuddy package validation")
    write_zip(output_dir, zip_path)
    write_individual_zips(skills_target, individual_dir)

    print(f"connector_dir={output_dir}")
    print(f"connector_zip={zip_path}")
    print(f"individual_zips={individual_dir}")
    print(f"entrypoint={root_skill_name}")
    print(
        "top_level_skills="
        f"{len(list(skills_target.glob('*/SKILL.md')))}"
    )
    print("validation=passed")


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    zip_path = (
        args.zip_path.expanduser().resolve()
        if args.zip_path
        else output_dir.with_suffix(".zip")
    )
    individual_dir = (
        args.individual_dir.expanduser().resolve()
        if args.individual_dir
        else output_dir.parent / f"{output_dir.name}-individual"
    )
    if not source.is_dir():
        print(f"ERROR: source directory does not exist: {source}", file=sys.stderr)
        return 2
    try:
        build(source, output_dir, zip_path, individual_dir)
    except (FileExistsError, ValidationFailure, ValueError, StopIteration) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
