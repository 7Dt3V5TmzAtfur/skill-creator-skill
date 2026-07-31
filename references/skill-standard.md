# LovStudio Skill Standard

This standard applies to public, paid, bundled, and internal LovStudio skills.
Its goal is portability first: a skill may carry LovStudio branding, but it
must not silently depend on Mark's local machine, workspace layout, or private
brand assets unless the skill is explicitly marked author-only.

## Source and Distribution Separation

Treat a Skill repository as two layers:

1. **Portable source** — canonical `SKILL.md`, scripts, references, assets, and
   embedded kit modules.
2. **Platform distribution** — generated metadata and archives for WorkBuddy
   or another marketplace.

Source `SKILL.md` top-level frontmatter is limited to `name`, `description`,
`license`, `allowed-tools`, and `metadata`. Put compatibility, version, tags,
and dependency declarations under `metadata`.

Platform-only fields such as `version`, `author`, `source_type`, `git_url`,
`clawhub_slug`, and `skillhub_slug` are injected into a distribution copy.
Never weaken the source standard to satisfy a single marketplace parser.

## Naming

- Use Agent Skills-compatible names: lowercase letters, numbers, and hyphens.
- Prefer `lovstudio-<name>` in `SKILL.md` frontmatter.
- Avoid namespace-style LovStudio names for new skills. Treat them as legacy aliases.
- Every source repo must live at `lovstudio/<name>-skill`. Repository placement
  is an invariant, not an interactive choice.
- Installed/distributed skill directories should resolve to
  `lovstudio-<name>/` so the directory and frontmatter name can match in user
  environments.

## Trigger Contract

Every Skill must include:

- A 50–200 character `description` that states what it does and when it applies.
- `## Triggers`.
- At least one concrete Chinese activation phrase.
- At least one concrete English activation phrase.
- Explicit non-trigger conditions for adjacent tasks.

The trigger contract is product routing, not marketing copy. It should prevent
both missed activation and accidental takeover of unrelated tasks.

## Skill Kits and Dependencies

Use a Skill Kit when a product has independently useful stages that users may
invoke alone or combine.

- `kit.yaml` declares the entrypoint, modules, module paths, and pipelines.
- Every module path must live inside the source repository.
- Every required module must be bundled into every platform release.
- Required dependencies live under `metadata.dependencies`.
- A platform build must fail early with the exact missing relative path.
- External sibling paths are never a valid release dependency.

Optional runtime capabilities may be documented as optional integrations, but
the core advertised workflow must remain executable from the submitted package.

## Runtime Portability

Skills must not assume these paths in execution instructions or scripts:

- personal home-directory absolute paths
- `~/lovstudio/...`
- `~/.claude/...` except in human-facing install examples
- `~/.agents/...` except in maintainer docs

Use this precedence whenever a skill needs user-specific paths, identity,
brand assets, or workspace settings:

1. Explicit CLI flags.
2. Environment variables.
3. User profile file.
4. Safe defaults such as the current working directory or an output directory
   under `$HOME/Documents`.
5. Ask the user once and explain what setting is missing.

## Publication Completion

Every released skill must be registered in the appropriate LovStudio catalog
and synchronized to `https://lovstudio.ai/skills`.

A publication is complete only when:

- The source release exists at `lovstudio/<name>-skill`.
- The catalog entry has reached the catalog repository's `main` branch.
- Relevant `skills-index`, catalog, detail, and cases cache tags are
  revalidated.
- `/skills/<name>` returns HTTP 200 and displays the released version.

For marketplace distributions, publication additionally requires:

- Standard YAML parsing succeeds without a fallback parser.
- First-listing source metadata is present.
- Every local Markdown, image, and module reference resolves inside the package.
- The package contains no caches, compiled Python files, private absolute paths,
  or unresolved placeholders.
- The final ZIP is rebuilt from a clean source checkout and validated as a
  package, not merely as source files.

## User Profile Contract

Portable skills may read a shared JSON profile at:

```bash
${LOVSTUDIO_SKILLS_PROFILE:-$HOME/.lovstudio/skills/profile.json}
```

Recommended fields:

```json
{
  "user": {
    "name": "Your Name",
    "language": "zh-CN",
    "timezone": "Asia/Shanghai"
  },
  "workspace": {
    "root": "$HOME/projects",
    "output_dir": "$HOME/Documents/lovstudio-skill-output"
  },
  "brand": {
    "name": "Your Brand",
    "site": "https://example.com",
    "profile": "$HOME/.lovstudio/skills/brand.json",
    "design_guide": "$HOME/.lovstudio/skills/design-guide.md"
  }
}
```

Environment variables override profile fields:

| Variable | Meaning |
|----------|---------|
| `LOVSTUDIO_SKILLS_PROFILE` | Path to the shared profile JSON |
| `LOVSTUDIO_SKILLS_HOME` | Shared LovStudio skills config/data directory |
| `LOVSTUDIO_SKILLS_INSTALL_DIR` | User's local agent skills installation directory |
| `LOVSTUDIO_SKILLS_WORKSPACE_ROOT` | User workspace root |
| `LOVSTUDIO_SKILLS_OUTPUT_DIR` | Default generated output directory |
| `LOVSTUDIO_SKILLS_BRAND_PROFILE` | Brand profile JSON or Markdown |
| `LOVSTUDIO_SKILLS_DESIGN_GUIDE` | Design guide path |

Skill-specific variables should use `LOVSTUDIO_<SKILL_NAME>_*`, for example
`LOVSTUDIO_MAINTAIN_PARTNERS_SITE_ROOT`. Avoid broad names such as
`PARTNERS_SITE_ROOT` and avoid pseudo-generic namespaces such as
`AGENT_SKILL_*` unless LovStudio is intentionally publishing a separate,
vendor-neutral standard.

Default files live under `~/.lovstudio/skills/` because these skills are
distributed by LovStudio. That directory is a storage namespace, not the public
API. Users can override it with `LOVSTUDIO_SKILLS_PROFILE`.

## Brand Coupling

Brand-aware skills should split their behavior into:

- Generic workflow: reusable by any user or brand.
- LovStudio defaults: optional profile/reference loaded only when configured.
- User initialization: a documented path for replacing LovStudio/Mark values
  with the user's own brand, workspace, design guide, and output directory.

If a skill is truly LovStudio-internal, say so in `metadata.compatibility` and
README.
Internal skills may use LovStudio paths, but they should still keep them in one
configuration section rather than scattering absolute paths across workflows.

## Scripts

- Scripts should accept explicit paths via CLI flags.
- Scripts should not import from private absolute paths.
- Scripts may use the shared profile contract, but missing profile values must
  produce actionable errors.
- Prefer `argparse` for Python CLIs.
- Validation and packaging scripts must use a standard YAML parser.
- Builders must copy from an allowlist, strip generated artifacts, and avoid
  mutating the canonical source `SKILL.md`.

## Migration Labels

Use these labels when auditing existing skills:

- `portable`: no local or brand-specific assumptions.
- `config-needed`: useful to public users, but needs a profile/env layer.
- `lovstudio-defaults`: generic core with optional LovStudio defaults.
- `author-only`: intentionally tied to Mark/LovStudio private workspace.
- `legacy-name`: still uses namespace-style or mismatched directory naming.
