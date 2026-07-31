# Tencent WorkBuddy Distribution Standard

Use this profile when the user selects Tencent WorkBuddy as a distribution
target. The source repository remains portable; WorkBuddy metadata is generated
into a separate package.

## Required source layout

```text
<name>-skill/
├── SKILL.md
├── README.md
├── scripts/
│   ├── validate_skill.py
│   └── build_workbuddy.py
├── workbuddy/
│   ├── connector-meta.json
│   └── icon.svg
├── kit.yaml                 # Skill Kit only
└── skills/                  # Skill Kit only
    └── <module>/SKILL.md
```

## Connector metadata

`workbuddy/connector-meta.json` must include:

- `name`, `name_zh`, `name_en`
- `description`, `description_zh`, `description_en`
- Globally unique kebab-case `source`
- `type: "skill-only"`
- SemVer `version`
- `source_type`
- One source locator: `git_url`, `clawhub_slug`, or `skillhub_slug`
- Two to five Chinese examples
- Two to five English examples
- `minWorkbuddyVersion` when a version-gated field is used

Display names should be 2–20 characters. Chinese and English connector
descriptions should each be 20–100 characters and state the user outcome.

## Skill frontmatter in the package

The builder converts portable source frontmatter into a WorkBuddy distribution
copy:

```yaml
---
name: lovstudio-<name>
description: <50-200 character capability and trigger description>
version: "0.1.0"
author: lovstudio
source_type: git
git_url: https://github.com/lovstudio/<name>-skill
---
```

The canonical source `SKILL.md` is not mutated.

## Explicit routing

Every submitted Skill needs:

- `## Triggers`
- Concrete Chinese and English activation phrases
- Explicit non-trigger conditions
- Concise capability boundaries
- Clear error handling and missing-resource messages

Descriptions and triggers must explain what the user can accomplish. Agent
count, internal architecture, background anecdotes, and implementation jargon
belong in technical documentation unless they materially affect user choice.

## Skill Kit completeness

WorkBuddy loads every Skill under `skills/`. A controller that references child
modules must ship those modules inside its own package:

```text
skills/lovstudio-<kit>/
├── SKILL.md
├── kit.yaml
└── skills/
    ├── <module-a>/SKILL.md
    └── <module-b>/SKILL.md
```

For every `kit.yaml` module:

- `modules[].path/SKILL.md` exists.
- The embedded frontmatter name matches `modules[].skill`.
- Every pipeline references known module IDs.
- The controller uses in-package paths.
- Missing modules cause a preflight error with the exact relative path.

An external sibling directory, a locally installed Skill, or an undocumented
runtime assumption does not satisfy package completeness.

## Package hygiene

Reject the build when it contains:

- `__pycache__`, `*.pyc`, `*.pyo`, or `.DS_Store`
- Private absolute user paths
- Unresolved `TODO` placeholders
- Broken Markdown links or case-image references
- External required module paths
- YAML that needs a fallback parser
- Missing source metadata

Use SVG for the market icon when possible. A simple 64×64 transparent icon is
preferred.

## Commands

Run from the source repository:

```bash
python3 scripts/validate_skill.py .
python3 scripts/validate_skill.py . --target workbuddy
python3 scripts/build_workbuddy.py . --output-dir dist/workbuddy
```

The builder validates the staged package again before writing
`dist/workbuddy.zip`. It also writes `dist/workbuddy-individual/*.zip`: the
controller ZIP embeds all required modules, while each module ZIP can be
installed and triggered independently.

## Submission evidence

Record:

- Source commit and version
- Source validation result
- WorkBuddy source-profile validation result
- Package validation result
- ZIP path and checksum
- Combined ZIP plus individual controller/module ZIP paths and checksums
- Top-level Skill/module count
- Connector metadata and icon presence
- Clean archive listing with no generated artifacts

Submit the emitted ZIP rather than a manually assembled directory.
