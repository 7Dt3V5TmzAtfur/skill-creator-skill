#!/usr/bin/env python3
"""Initialize a release-ready LovStudio Skill or Skill Kit source repository."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Optional, Tuple


SKILL_MD = """---
name: lovstudio-{name}
description: >
  TODO：用 50–200 个字符说明这个 Skill 能完成什么、适用于哪些输入或任务，
  并自然包含用户会说出的中文与 English 触发语句。
license: MIT
metadata:
  author: lovstudio
  version: "0.1.0"
  tags:
    - TODO
  compatibility: "Portable Agent Skills format. TODO: list runtime requirements."
  dependencies: []
---

# {title}

TODO：用一到两句话说明用户得到的结果，不要把内部背景或实现细节写进用户制品。

## Triggers

### Activate when

- TODO：列出明确中文触发语，例如“帮我……”
- TODO: list an explicit English trigger phrase.

### Do not activate when

- TODO：列出相邻但不属于本 Skill 的任务，并说明应交给什么能力。

## User Configuration

This skill must not assume a private workspace, personal absolute paths, or a
fixed agent runtime path. If user-specific paths or brand settings are needed,
follow `references/user-config.md`.

{kit_section}## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve skill root, dependencies, and user config

- Use `SKILL_DIR` if the environment provides it.
- Otherwise infer the installed skill directory from the current skill context.
- Verify every required local module, reference, script, and asset before work.
- If a required resource is missing, name its expected relative path and stop
  before producing a partial result.

When running scripts manually:

```bash
export SKILL_DIR="/path/to/lovstudio-{name}"
```

If user-specific fields are missing, ask once and map the answer to CLI flags,
environment variables, or the shared profile described in
`references/user-config.md`.

### Step 1: Understand the requested outcome

- Separate internal context from user-visible output.
- Confirm the input, intended audience, expected deliverable, and evidence gaps.

### Step 2: Execute the deterministic workflow

```bash
python3 "$SKILL_DIR/scripts/TODO.py" --input INPUT --output OUTPUT
```

### Step 3: Validate the deliverable

- Verify completeness, factual support, user-visible copy, and output paths.
- Report concrete files or results, plus any remaining evidence gaps.

## CLI Reference

| Argument | Default | Description |
|----------|---------|-------------|
| `--input` | required | TODO |
| `--output` | `output.ext` | TODO |

## Dependencies

Runtime dependencies:

```bash
pip install TODO
```
"""

KIT_SECTION = """## Skill Kit Modules

This repository is a self-contained Skill Kit. At Step 0, load and verify:

{module_lines}

`kit.yaml` is the machine-readable module and pipeline manifest. Every module
listed there must ship inside this repository and every release archive.

"""

README_MD = """# lovstudio-{name}

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

TODO: One-line description focused on the user's outcome.

Part of [LovStudio Skills](https://lovstudio.ai/skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
git clone https://github.com/lovstudio/{name}-skill "${{LOVSTUDIO_SKILLS_INSTALL_DIR:?Set LOVSTUDIO_SKILLS_INSTALL_DIR}}/lovstudio-{name}"
```

## Configuration

This skill is portable by default. User-specific paths and brand settings
should be provided through CLI flags, environment variables, or:

```bash
${{LOVSTUDIO_SKILLS_PROFILE:-$HOME/.lovstudio/skills/profile.json}}
```

See `references/user-config.md`.

## Usage

```bash
SKILL_DIR="${{LOVSTUDIO_SKILLS_INSTALL_DIR:?Set LOVSTUDIO_SKILLS_INSTALL_DIR}}/lovstudio-{name}"
python3 "$SKILL_DIR/scripts/TODO.py" --input INPUT --output OUTPUT
```

## Quality Gate

```bash
python3 scripts/validate_skill.py .
{workbuddy_validation}
```

## License

MIT
"""

KIT_YAML = """name: {name}
display_name: "TODO"
version: "0.1.0"
entrypoint: lovstudio-{name}
modules:
{module_entries}
pipelines:
  full:
{pipeline_entries}
"""

WORKBUDDY_META = """{{
  "name": "TODO",
  "name_zh": "TODO",
  "name_en": "TODO",
  "description": "TODO: concise default description.",
  "description_zh": "TODO：用 20–100 个字符说明核心能力和用户结果。",
  "description_en": "TODO: describe the core capability and user outcome in 20-100 characters.",
  "source": "lovstudio-{name}",
  "type": "skill-only",
  "version": "0.1.0",
  "source_type": "git",
  "git_url": "https://github.com/lovstudio/{name}-skill",
  "minWorkbuddyVersion": "4.24.0",
  "examples_zh": [
    "TODO：提供一个真实的中文使用示例",
    "TODO：提供第二个不同场景的中文使用示例"
  ],
  "examples_en": [
    "TODO: provide one realistic English usage example",
    "TODO: provide a second English usage example"
  ]
}}
"""

WORKBUDDY_README = """# WorkBuddy distribution

This directory contains platform metadata and the market icon. Before building:

1. Replace every `TODO` in `connector-meta.json`.
2. Replace `icon.svg` with the final 64×64 brand icon if needed.
3. Ensure every Skill description is 50–200 characters.
4. Run the source and WorkBuddy validation commands from the repository root.

Build a self-contained upload ZIP:

```bash
python3 scripts/build_workbuddy.py . --output-dir dist/workbuddy
```

The builder injects WorkBuddy-only frontmatter fields into the distribution
copy, bundles every `kit.yaml` module, rejects broken local references and
removes generated cache files. It emits one combined Connector ZIP plus one
independently installable ZIP for the controller and every module.
"""

WORKBUDDY_ICON = """<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="16" fill="#0B5D43"/>
  <path d="M18 19h9l5 9 5-9h9L35 45h-6L18 19Z" fill="#F7F4EC"/>
</svg>
"""

WORKBUDDY_WORKFLOW = """name: Validate WorkBuddy distribution

on:
  push:
  pull_request:

jobs:
  validate-workbuddy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python -m pip install PyYAML
      - run: python scripts/validate_skill.py . --target workbuddy
      - run: python scripts/build_workbuddy.py . --output-dir dist/workbuddy
"""

GITIGNORE = """__pycache__/
*.pyc
*.pyo
.DS_Store
.venv/
venv/
node_modules/
.env
.env.local
dist/
"""

LICENSE_MD = """MIT License

Copyright (c) 2026 LovStudio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

CHANGELOG_MD = """# Changelog

## 0.1.0

- Initial independent skill release.
"""

VALIDATE_WORKFLOW = """name: Validate skill

on:
  push:
  pull_request:

jobs:
  validate-agent-skills:
    uses: lovstudio/dev-skills/.github/workflows/validate-skill.yml@main
    with:
      skill_name: lovstudio-{name}
  validate-lovstudio:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python -m pip install PyYAML
      - run: python scripts/validate_skill.py .
"""

USER_CONFIG_MD = """# User Configuration

This skill follows the portable Agent Skill profile contract. It must not
assume a private workspace, personal absolute paths, or private brand assets.

## Resolution Order

1. Explicit CLI flags.
2. Environment variables.
3. Shared profile JSON.
4. Safe defaults such as the current working directory or `$HOME/Documents`.
5. Ask the user once for missing required fields.

## Shared Profile

Default profile path:

```bash
${{LOVSTUDIO_SKILLS_PROFILE:-$HOME/.lovstudio/skills/profile.json}}
```

Example:

```json
{{
  "user": {{
    "name": "Your Name",
    "language": "zh-CN",
    "timezone": "Asia/Shanghai"
  }},
  "workspace": {{
    "root": "$HOME/projects",
    "output_dir": "$HOME/Documents/lovstudio-skill-output"
  }},
  "brand": {{
    "name": "Your Brand",
    "site": "https://example.com"
  }}
}}
```
"""


def _expand_path(value: str) -> Path:
    return Path(os.path.expandvars(value)).expanduser()


def _nested(data: dict, dotted: str) -> Optional[str]:
    cur = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return str(cur) if cur else None


def _load_profile() -> Tuple[Path, dict]:
    profile = _expand_path(
        os.environ.get("LOVSTUDIO_SKILLS_PROFILE")
        or str(Path.home() / ".lovstudio/skills/profile.json")
    )
    if not profile.exists():
        return profile, {}
    try:
        return profile, json.loads(profile.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON in {profile}: {exc}", file=sys.stderr)
        sys.exit(1)


def _profile_first(data: dict, keys: Tuple[str, ...]) -> Optional[str]:
    for key in keys:
        value = _nested(data, key)
        if value:
            return value
    return None


def resolve_base(cli_path: str) -> Path:
    if cli_path:
        return _expand_path(cli_path)
    _, profile = _load_profile()
    if os.environ.get("LOVSTUDIO_SKILL_CREATOR_REPOS_ROOT"):
        return _expand_path(os.environ["LOVSTUDIO_SKILL_CREATOR_REPOS_ROOT"])
    profile_value = _profile_first(
        profile,
        (
            "lovstudio.skill_repos_root",
            "skills.repos_root",
            "workspace.skill_repos_root",
            "workspace.skills_root",
        ),
    )
    return _expand_path(profile_value) if profile_value else Path.cwd()


def normalize_name(value: str) -> str:
    name = value
    if name.startswith("lovstudio-"):
        name = name[len("lovstudio-") :]
    if name.endswith("-skill"):
        name = name[: -len("-skill")]
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise ValueError(
            "skill name must use lowercase letters, numbers, and single hyphens only"
        )
    return name


def write_skill(path: Path, name: str, kit_section: str = "") -> None:
    path.write_text(
        SKILL_MD.format(
            name=name,
            title=f"lovstudio-{name} — TODO",
            kit_section=kit_section,
        ),
        encoding="utf-8",
    )


def render_kit(name: str, modules: list[str]) -> tuple[str, str]:
    module_lines = "\n".join(
        f"- `$SKILL_DIR/skills/{module}/SKILL.md` — `lovstudio-{module}`"
        for module in modules
    )
    module_entries = "\n".join(
        "  - id: {module}\n"
        "    skill: lovstudio-{module}\n"
        "    path: skills/{module}".format(module=module)
        for module in modules
    )
    pipeline_entries = "\n".join(f"    - {module}" for module in modules)
    return (
        KIT_SECTION.format(module_lines=module_lines),
        KIT_YAML.format(
            name=name,
            module_entries=module_entries,
            pipeline_entries=pipeline_entries,
        ),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Initialize a LovStudio Skill or self-contained Skill Kit."
    )
    parser.add_argument("name", help="Short name without lovstudio- or -skill")
    parser.add_argument("--path", default="", help="Custom parent directory")
    parser.add_argument("--paid", action="store_true", help="Use private repo hint")
    parser.add_argument(
        "--kit",
        action="store_true",
        help="Create a Skill Kit controller and embedded child modules",
    )
    parser.add_argument(
        "--module",
        action="append",
        default=[],
        help="Embedded module short name; repeat for each module (requires --kit)",
    )
    parser.add_argument(
        "--distribution",
        choices=("source", "workbuddy"),
        default="source",
        help="Add a platform distribution profile (default: source only)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        name = normalize_name(args.name)
        modules = [normalize_name(module) for module in args.module]
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.module and not args.kit:
        print("ERROR: --module requires --kit", file=sys.stderr)
        return 1
    if args.kit and not modules:
        print("ERROR: --kit requires at least one --module", file=sys.stderr)
        return 1
    if len(set(modules)) != len(modules):
        print("ERROR: module names must be unique", file=sys.stderr)
        return 1
    if name in modules:
        print(
            "ERROR: a module name must differ from the controller name",
            file=sys.stderr,
        )
        return 1

    base = resolve_base(args.path)
    base.mkdir(parents=True, exist_ok=True)
    skill_dir = base / f"{name}-skill"
    if skill_dir.exists():
        print(f"ERROR: {skill_dir} already exists", file=sys.stderr)
        return 1

    skill_dir.mkdir()
    for directory in ("scripts", "references", ".github/workflows"):
        (skill_dir / directory).mkdir(parents=True, exist_ok=True)

    kit_section = ""
    if args.kit:
        kit_section, kit_text = render_kit(name, modules)
        (skill_dir / "kit.yaml").write_text(kit_text, encoding="utf-8")
        for module in modules:
            module_dir = skill_dir / "skills" / module
            module_dir.mkdir(parents=True)
            write_skill(module_dir / "SKILL.md", module)

    write_skill(skill_dir / "SKILL.md", name, kit_section)
    workbuddy_validation = ""
    if args.distribution == "workbuddy":
        workbuddy_validation = (
            "python3 scripts/validate_skill.py . --target workbuddy\n"
            "python3 scripts/build_workbuddy.py . --output-dir dist/workbuddy"
        )
    (skill_dir / "README.md").write_text(
        README_MD.format(
            name=name,
            workbuddy_validation=workbuddy_validation,
        ),
        encoding="utf-8",
    )
    (skill_dir / "references" / "user-config.md").write_text(
        USER_CONFIG_MD, encoding="utf-8"
    )
    (skill_dir / ".gitignore").write_text(GITIGNORE, encoding="utf-8")
    (skill_dir / "LICENSE").write_text(LICENSE_MD, encoding="utf-8")
    (skill_dir / "CHANGELOG.md").write_text(CHANGELOG_MD, encoding="utf-8")
    (skill_dir / ".github" / "workflows" / "validate.yml").write_text(
        VALIDATE_WORKFLOW.format(name=name), encoding="utf-8"
    )

    script_root = Path(__file__).resolve().parent
    shutil.copy2(script_root / "validate_skill.py", skill_dir / "scripts")
    if args.distribution == "workbuddy":
        workbuddy_dir = skill_dir / "workbuddy"
        workbuddy_dir.mkdir()
        (workbuddy_dir / "connector-meta.json").write_text(
            WORKBUDDY_META.format(name=name), encoding="utf-8"
        )
        (workbuddy_dir / "icon.svg").write_text(WORKBUDDY_ICON, encoding="utf-8")
        (workbuddy_dir / "README.md").write_text(
            WORKBUDDY_README, encoding="utf-8"
        )
        shutil.copy2(script_root / "build_workbuddy.py", skill_dir / "scripts")
        (skill_dir / ".github" / "workflows" / "workbuddy.yml").write_text(
            WORKBUDDY_WORKFLOW, encoding="utf-8"
        )

    kind = "Skill Kit" if args.kit else "Skill"
    print(f"✓ Created {kind}: {skill_dir}/")
    print("  Source validation: python3 scripts/validate_skill.py .")
    if args.distribution == "workbuddy":
        print(
            "  WorkBuddy gate: python3 scripts/validate_skill.py . --target workbuddy"
        )
        print(
            "  WorkBuddy ZIP:  python3 scripts/build_workbuddy.py . "
            "--output-dir dist/workbuddy"
        )
    print()
    print("Next steps:")
    print("  1. Replace every TODO and implement the workflow")
    print("  2. Run the quality gates until all checks pass")
    print("  3. git init && git add -A && git commit -m 'feat: initial release'")
    visibility = "--private" if args.paid else "--public"
    print(
        f"  4. gh repo create lovstudio/{name}-skill {visibility} --source=. --push"
    )
    print("  5. Tag v0.1.0, register the catalog, and verify lovstudio.ai")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
