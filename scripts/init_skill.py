#!/usr/bin/env python3
"""
Initialize a new lovstudio skill scaffold.

Usage:
    python3 init_skill.py <name>
    python3 init_skill.py <name> --paid
    python3 init_skill.py <name> --path /custom/path

Examples:
    python3 init_skill.py fill-form
        → <configured repos root>/fill-form-skill/
    python3 init_skill.py any2pptx
        → <configured repos root>/any2pptx-skill/
Default base directories resolve from --path, LOVSTUDIO_SKILL_CREATOR_* env
vars, the shared profile JSON, then a safe current-directory fallback.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional, Tuple

SKILL_MD = '''---
name: lovstudio-{name}
description: >
  TODO: What this skill does (1-2 sentences).
  TODO: When to trigger — specific scenarios, file types, user phrases.
  Also trigger when the user mentions "TODO_CN", "TODO_EN".
license: MIT
compatibility: >
  Portable Agent Skills format. TODO: Requires Python 3.8+ and <library>.
  User-specific paths, brand assets, and workspace settings must come from
  explicit CLI flags, environment variables, or the shared user profile.
# Optional: declare required skill-level dependencies by exact SKILL.md
# frontmatter name. Example:
# depends_on:
#   - lovstudio-<other-skill>
metadata:
  author: lovstudio
  version: "0.1.0"
  tags: TODO
---

# {name} — TODO: Short Title

TODO: 1-2 sentence overview.

## User Configuration

This skill must not assume a private workspace, personal absolute paths, or a
fixed agent runtime path. If user-specific paths or brand settings are needed,
follow `references/user-config.md`.

## When to Use

- TODO: Scenario 1
- TODO: Scenario 2

## Workflow (MANDATORY)

**You MUST follow these steps in order:**

### Step 0: Resolve skill root and user config

- Use `SKILL_DIR` if the environment provides it.
- Otherwise infer the installed skill directory from the current skill context.
- When running scripts manually, set it explicitly:

```bash
export SKILL_DIR="/path/to/lovstudio-{name}"
```

If user-specific fields are missing, ask once and map the answer to CLI flags,
environment variables, or the shared profile described in
`references/user-config.md`.

### Step 1: TODO

```bash
python3 "$SKILL_DIR/scripts/TODO.py" --help
```

### Step 2: Ask the user when needed

**IMPORTANT: Use `AskUserQuestion` to collect options BEFORE running.**

### Step 3: Execute

```bash
python3 "$SKILL_DIR/scripts/TODO.py" --input <path> --output <path>
```

## CLI Reference

| Argument | Default | Description |
|----------|---------|-------------|
| `--input` | (required) | TODO |
| `--output` | `output.ext` | TODO |

## Dependencies

```bash
pip install TODO --break-system-packages
```
'''

README_MD = '''# lovstudio-{name}

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

TODO: One-line description.

Part of [lovstudio general skills](https://github.com/lovstudio/general-skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
git clone https://github.com/lovstudio/{name}-skill "${{LOVSTUDIO_SKILLS_INSTALL_DIR:?Set LOVSTUDIO_SKILLS_INSTALL_DIR}}/lovstudio-{name}"
```

Requires: Python 3.8+ and `pip install TODO`

## Configuration

This skill is portable by default. User-specific paths and brand settings should
be provided through CLI flags, environment variables, or:

```bash
${{LOVSTUDIO_SKILLS_PROFILE:-$HOME/.lovstudio/skills/profile.json}}
```

See `references/user-config.md`.

## Usage

```bash
SKILL_DIR="${{LOVSTUDIO_SKILLS_INSTALL_DIR:?Set LOVSTUDIO_SKILLS_INSTALL_DIR}}/lovstudio-{name}"
python3 "$SKILL_DIR/scripts/TODO.py" --input file.ext --output result.ext
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--input` | (required) | TODO |
| `--output` | `output.ext` | TODO |

## License

MIT
'''

GITIGNORE = '''__pycache__/
*.pyc
*.pyo
.DS_Store
.venv/
venv/
node_modules/
.env
.env.local
'''

LICENSE_MD = '''MIT License

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
'''

CHANGELOG_MD = '''# Changelog

## 0.1.0

- Initial independent skill release.
'''

VALIDATE_WORKFLOW = '''name: Validate skill

on:
  push:
  pull_request:

jobs:
  validate:
    uses: lovstudio/dev-skills/.github/workflows/validate-skill.yml@main
    with:
      skill_name: lovstudio-{name}
'''

USER_CONFIG_MD = '''# User Configuration

This skill follows the portable agent skill profile contract. It must not
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
    "site": "https://example.com",
    "profile": "$HOME/.lovstudio/skills/brand.json",
    "design_guide": "$HOME/.lovstudio/skills/design-guide.md"
  }}
}}
```

Environment variable overrides:

| Variable | Meaning |
|----------|---------|
| `LOVSTUDIO_SKILLS_PROFILE` | Path to the shared profile JSON |
| `LOVSTUDIO_SKILLS_HOME` | Shared LovStudio skills config/data directory |
| `LOVSTUDIO_SKILLS_WORKSPACE_ROOT` | User workspace root |
| `LOVSTUDIO_SKILLS_OUTPUT_DIR` | Default generated output directory |
| `LOVSTUDIO_SKILLS_BRAND_PROFILE` | Brand profile JSON or Markdown |
| `LOVSTUDIO_SKILLS_DESIGN_GUIDE` | Design guide path |

## Implementation Notes

- Scripts should accept explicit paths via CLI flags.
- Missing profile fields should produce actionable errors.
- LovStudio maintainer defaults belong in an optional profile, not in the workflow.
'''


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
        return profile, json.loads(profile.read_text())
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
    env_key = "LOVSTUDIO_SKILL_CREATOR_REPOS_ROOT"
    profile_keys = (
        "lovstudio.skill_repos_root",
        "skills.repos_root",
        "workspace.skill_repos_root",
        "workspace.skills_root",
    )

    if os.environ.get(env_key):
        return _expand_path(os.environ[env_key])

    profile_value = _profile_first(profile, profile_keys)
    if profile_value:
        return _expand_path(profile_value)

    return Path.cwd()


def main():
    ap = argparse.ArgumentParser(
        description=(
            "Initialize a new independent lovstudio/{name}-skill source repository"
        )
    )
    ap.add_argument("name", help="Skill short name (no prefix / no -skill suffix)")
    ap.add_argument(
        "--path",
        default="",
        help=(
            "Custom base directory. Defaults resolve from LOVSTUDIO_SKILL_CREATOR_* env, "
            "the shared profile JSON, then a safe current-directory fallback."
        ),
    )
    ap.add_argument("--paid", action="store_true", help="Mark as paid in hints (actual paid flag lives in lovstudio-general-skills/skills.yaml)")
    args = ap.parse_args()

    # Normalize: strip common prefixes / suffix users might paste
    name = args.name
    for pfx in ("lovstudio-",):
        if name.startswith(pfx):
            name = name[len(pfx):]
    if name.endswith("-skill"):
        name = name[: -len("-skill")]
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        print(
            "ERROR: skill name must use lowercase letters, numbers, and single hyphens only",
            file=sys.stderr,
        )
        sys.exit(1)

    base = resolve_base(args.path)
    base.mkdir(parents=True, exist_ok=True)
    skill_dir = base / f"{name}-skill"

    if skill_dir.exists():
        print(f"ERROR: {skill_dir} already exists", file=sys.stderr)
        sys.exit(1)

    skill_dir.mkdir()
    (skill_dir / "scripts").mkdir()
    (skill_dir / "references").mkdir()
    (skill_dir / ".github" / "workflows").mkdir(parents=True)

    (skill_dir / "SKILL.md").write_text(SKILL_MD.format(name=name))
    (skill_dir / "README.md").write_text(README_MD.format(name=name))
    (skill_dir / "references" / "user-config.md").write_text(USER_CONFIG_MD.format(name=name))
    (skill_dir / ".gitignore").write_text(GITIGNORE)
    (skill_dir / "LICENSE").write_text(LICENSE_MD)
    (skill_dir / "CHANGELOG.md").write_text(CHANGELOG_MD)
    (skill_dir / ".github" / "workflows" / "validate.yml").write_text(
        VALIDATE_WORKFLOW.format(name=name)
    )

    print(f"✓ Created {skill_dir}/")
    print(f"  SKILL.md      — AI-facing frontmatter + workflow")
    print(f"  README.md     — human-facing GitHub docs")
    print(f"  references/   — user configuration contract")
    print(f"  scripts/      — add Python CLI scripts here")
    print(f"  .gitignore")
    print()
    print("Next steps:")
    print(f"  1. cd {skill_dir}")
    print(f"  2. Implement scripts/ and fill TODO placeholders in SKILL.md / README.md")
    print(f"  3. git init && git add -A && git commit -m 'feat: initial release of {name} skill'")
    visibility = "--private" if args.paid else "--public"
    print(f"  4. gh repo create lovstudio/{name}-skill {visibility} --source=. --push")
    print(f"  5. Tag and publish v0.1.0 so aggregate mirrors can sync the release")
    print(f"  6. Install or symlink {skill_dir} into your agent's skills directory as lovstudio-{name}")
    paid_flag = "true" if args.paid else "false"
    print(f"  7. Register in the appropriate catalog (paid: {paid_flag})")
    print(f"  8. Revalidate and verify https://lovstudio.ai/skills/{name}")


if __name__ == "__main__":
    main()
