#!/usr/bin/env python3
"""Regression tests for the completable scaffold and the release gate."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "scripts" / "init_skill.py"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        env=dict(os.environ),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


class ScaffoldGateTests(unittest.TestCase):
    def create(self, workspace: Path, *extra: str, name: str = "demo") -> Path:
        result = run(
            [
                sys.executable,
                str(INIT),
                name,
                "--path",
                str(workspace),
                *extra,
            ]
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return workspace / f"{name}-skill"

    def validate(self, source: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        return run(
            [sys.executable, str(source / "scripts" / "validate_skill.py"), str(source), *extra]
        )

    def test_fresh_scaffold_passes_local_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = self.create(Path(temporary))
            result = self.validate(source)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PASSED", result.stdout)
            self.assertNotIn("FAILED", result.stdout)

    def test_strict_gate_rejects_scaffold_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = self.create(Path(temporary))
            result = self.validate(source, "--strict")
            self.assertEqual(result.returncode, 1)
            self.assertIn("scaffold", result.stdout)

    def test_scaffold_case_records_the_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            import json

            source = self.create(Path(temporary))
            cases = json.loads((source / "cases" / "cases.json").read_text(encoding="utf-8"))
            self.assertTrue(cases)
            self.assertIs(cases[0].get("scaffold"), True)
            card = (source / "skill-card.yaml").read_text(encoding="utf-8")
            self.assertIn("scaffold: true", card)

    def test_kit_modules_inherit_the_controller_trust_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = self.create(
                Path(temporary),
                "--kit",
                "--module",
                "research",
                "--module",
                "draft",
                name="publishing",
            )
            module = source / "skills" / "draft"
            self.assertFalse((module / "skill-card.yaml").exists())
            self.assertTrue((source / "skill-card.yaml").is_file())
            result = self.validate(source)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_module_cards_are_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = self.create(
                Path(temporary),
                "--kit",
                "--module",
                "alpha",
                "--with-module-cards",
                name="pubkit",
            )
            self.assertTrue((source / "skills" / "alpha" / "skill-card.yaml").is_file())

    def test_install_falls_back_when_symlink_is_denied(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            import init_skill
        finally:
            sys.path.pop(0)
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            source = workspace / "src-skill"
            source.mkdir()
            (source / "SKILL.md").write_text("ok", encoding="utf-8")
            original = Path.symlink_to

            def denied(self, target, target_is_directory=False):
                raise OSError("symlink privilege required")

            Path.symlink_to = denied
            try:
                mode = init_skill.link_source(source.resolve(), workspace / "installed")
            finally:
                Path.symlink_to = original
            self.assertIn(mode, {"junction", "copy"})
            self.assertTrue((workspace / "installed").is_dir())


if __name__ == "__main__":
    unittest.main()
