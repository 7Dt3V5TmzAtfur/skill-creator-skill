# Migration Notes

## 2026-07: one source path, no repository-target prompt

The creator no longer exposes `--target`, `--dev-skills`, or a repository
choice in the interactive flow. Every scaffold is created as the source for
`lovstudio/<name>-skill`.

General-skills and dev-skills are downstream distribution indexes. Register
them after the independent repo is released; do not treat either catalog as a
scaffold destination.

## 2026-07: independent sources with a generated dev-skills aggregate

Every skill now has one source of truth: `lovstudio/<name>-skill`. Free Meta /
Dev Tools skills may be listed in `lovstudio/dev-skills`, whose checked-in
skill directories are generated from the latest GitHub Releases.

Do not use `--target dev-skills` and do not edit aggregate mirror directories
as source. Create and release the independent repo, register it in
`independent-skills.json` and `skills.yaml`, then let the sync workflow update
the mirror.

## 2026-05: dev-skills aggregate target (superseded)

The direct-source aggregate model below is retained only as historical context
and must not be used for new work:

```bash
python3 ~/.claude/skills/lovstudio-skill-creator/scripts/init_skill.py tanstack-query --target dev-skills
```

The skill directory is:

```text
~/lovstudio/coding/lovstudio-dev-skills/skills/tanstack-query/
```

`skills.yaml` must include:

```yaml
repo: lovstudio/dev-skills
skill_path: skills/tanstack-query
```

## 2026-04: independent per-skill repos

The ecosystem was refactored from a monorepo (`lovstudio/skills` containing
`skills/lovstudio-<name>/`) + mirror (`lovstudio/pro-skills`) into independent
per-skill repos + central index. The old `lovstudio/pro-skills` was archived.

If working on a legacy skill still in the old structure, migrate it first:

```bash
# 1. Extract from monorepo subdirectory
cp -r ~/projects/lovstudio-skills/skills/lovstudio-<name> \
      ~/lovstudio/coding/skills/<name>-skill
cd ~/lovstudio/coding/skills/<name>-skill

# 2. Fresh git history
rm -rf .git
git init && git add -A && git commit -m "import: <name> from monorepo"

# 3. Create independent repo
gh repo create lovstudio/<name>-skill --public --source=. --push
```
