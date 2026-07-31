# Templates

`scripts/init_skill.py` is the source of truth for generated files. These
examples explain the contracts; update the script first when templates change.

## Source SKILL.md

```yaml
---
name: lovstudio-<name>
description: >
  Use 50-200 characters to explain the outcome, supported inputs, and concrete
  Chinese and English trigger phrases.
license: MIT
metadata:
  author: lovstudio
  version: "0.1.0"
  tags:
    - <tag>
  compatibility: "Portable Agent Skills format. List runtime requirements."
  dependencies: []
---
```

The source top level is intentionally limited to Agent Skills-compatible keys:

- `name`
- `description`
- `license`
- `allowed-tools`
- `metadata`

Place compatibility and required dependencies under `metadata`. Platform-only
fields are generated into distribution copies.

Required body sections:

```markdown
# <Outcome-focused title>

## Triggers

### Activate when

- <Chinese user phrase>
- <English user phrase>

### Do not activate when

- <Adjacent task that belongs elsewhere>

## Workflow (MANDATORY)

### Step 0: Resolve skill root, dependencies, and user config

Verify every required module, reference, script, and asset before execution.
If anything is missing, name the expected relative path and stop before
producing a partial result.
```

## Skill Kit

Create a kit with:

```bash
python3 scripts/init_skill.py <name> \
  --kit \
  --module <module-a> \
  --module <module-b>
```

The generated `kit.yaml` is the machine-readable contract:

```yaml
name: <name>
display_name: "<display name>"
version: "0.1.0"
entrypoint: lovstudio-<name>
modules:
  - id: <module-a>
    skill: lovstudio-<module-a>
    path: skills/<module-a>
pipelines:
  full:
    - <module-a>
```

Every `modules[].path` must contain a `SKILL.md` inside the same source
repository and release archive.

## WorkBuddy distribution

Create the platform profile with:

```bash
python3 scripts/init_skill.py <name> --distribution workbuddy
```

Or combine it with Skill Kit flags. Generated platform files:

```text
workbuddy/
├── connector-meta.json
├── icon.svg
└── README.md
scripts/
├── validate_skill.py
└── build_workbuddy.py
```

The source `SKILL.md` remains portable. The builder creates a distribution copy
whose frontmatter includes:

```yaml
---
name: lovstudio-<name>
description: <50-200 character Skill description>
version: "0.1.0"
author: lovstudio
source_type: git
git_url: https://github.com/lovstudio/<name>-skill
---
```

Build only after both gates pass:

```bash
python3 scripts/validate_skill.py .
python3 scripts/validate_skill.py . --target workbuddy
python3 scripts/build_workbuddy.py . --output-dir dist/workbuddy
```

The build emits a combined Connector ZIP and `dist/workbuddy-individual/*.zip`
for users who want only the controller or one module.

## README.md

Every LovStudio source repository includes:

- Version badge matching `metadata.version`
- User-outcome description
- Install and configuration instructions
- Usage example
- Source and platform quality-gate commands
- MIT license section

## Notes

- Source repository: `lovstudio/<name>-skill`.
- Installed directory and source frontmatter name: `lovstudio-<name>`.
- Start at `0.1.0`.
- `paid` lives only in `lovstudio/general-skills` catalog metadata.
- `__pycache__`, `*.pyc`, `*.pyo`, `.DS_Store`, private absolute paths, and
  unresolved TODOs never enter a release.
- Publication completes only after the tagged source, catalog, live
  `lovstudio.ai/skills/<name>` page, and any platform ZIP are independently
  verified.
