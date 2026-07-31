# lovstudio-skill-creator

![Version](https://img.shields.io/badge/version-3.0.0-CC785C)

Scaffold release-ready LovStudio Skills and self-contained Skill Kits as
independent GitHub repositories. The v3 workflow separates portable source
metadata from platform distributions, validates routing and dependencies, and
builds Tencent WorkBuddy upload ZIPs without manual assembly.

Part of [LovStudio Skills](https://lovstudio.ai/skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
git clone https://github.com/lovstudio/skill-creator-skill \
  "${LOVSTUDIO_SKILLS_INSTALL_DIR:?Set LOVSTUDIO_SKILLS_INSTALL_DIR}/lovstudio-skill-creator"
```

## Quick Start

Single portable Skill:

```bash
python3 "$SKILL_DIR/scripts/init_skill.py" wcx
```

Self-contained Skill Kit for WorkBuddy:

```bash
python3 "$SKILL_DIR/scripts/init_skill.py" bp \
  --kit \
  --module bp-outline \
  --module bp-deck \
  --module bp-polish \
  --distribution workbuddy
```

The second command generates:

```text
bp-skill/
├── SKILL.md
├── README.md
├── kit.yaml
├── skills/
│   ├── bp-outline/SKILL.md
│   ├── bp-deck/SKILL.md
│   └── bp-polish/SKILL.md
├── workbuddy/
│   ├── connector-meta.json
│   └── icon.svg
└── scripts/
    ├── validate_skill.py
    └── build_workbuddy.py
```

Fill the generated placeholders, then:

```bash
python3 scripts/validate_skill.py .
python3 scripts/validate_skill.py . --target workbuddy
python3 scripts/build_workbuddy.py . --output-dir dist/workbuddy
```

The last command writes a validated, self-contained `dist/workbuddy.zip` and
individual controller/module ZIPs under `dist/workbuddy-individual/`.

## Architecture

| Layer | Location | Purpose |
|-------|----------|---------|
| Source repository | `lovstudio/<name>-skill` | Canonical portable Skill or Skill Kit |
| General catalog | `lovstudio/general-skills` | Public index and commercial metadata |
| Dev bundle | `lovstudio/dev-skills` | Generated mirror of tagged releases |
| WorkBuddy profile | `<name>-skill/workbuddy` | Connector metadata and market icon |
| Agent runtime | Installed `lovstudio-<name>` directory | Local execution |

Every source repository is independent. Catalogs, bundles, marketplace ZIPs,
and local installs are downstream distributions.

## Source and Distribution Contract

- Canonical `SKILL.md` uses only Agent Skills-compatible top-level keys.
- Compatibility, version, tags, and dependencies live under `metadata`.
- WorkBuddy-only version, author, and source fields are injected into the
  distribution copy.
- Every Skill has explicit activation and non-trigger conditions.
- Every Skill Kit embeds required modules and declares them in `kit.yaml`.
- Builders reject broken references, private paths, placeholders, caches, and
  non-standard YAML before producing a ZIP.

`paid: true/false` lives only in `lovstudio/general-skills` catalog metadata.
User paths and brand settings come from CLI flags, environment variables, or
`${LOVSTUDIO_SKILLS_PROFILE:-$HOME/.lovstudio/skills/profile.json}`.

## Release

1. Validate source and every enabled distribution target.
2. Commit and create `lovstudio/<name>-skill`.
3. Tag the release.
4. Register the appropriate catalogs.
5. Revalidate and verify `https://lovstudio.ai/skills/<name>`.
6. Submit the generated platform archive with commit, version, and checksum.

## License

MIT
