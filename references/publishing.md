# Publishing to lovstudio.ai/skills

Use this workflow after the source release and catalog change have reached
their respective `main` branches.

## Revalidate

Resolve `LOVSTUDIO_REVALIDATE_SECRET` from the configured environment or web
deployment settings. Never print it.

Replace `<catalog>` with `general` or `dev`:

```bash
test -n "$LOVSTUDIO_REVALIDATE_SECRET"

curl -fsS -X POST https://lovstudio.ai/api/revalidate \
  -H "x-revalidate-secret: $LOVSTUDIO_REVALIDATE_SECRET" \
  -H "content-type: application/json" \
  -d '{
    "tags":[
      "skills-index",
      "skills-index:<catalog>",
      "skill:<name>",
      "skill-cases:<name>"
    ],
    "paths":[
      "/skills",
      "/skills/<name>",
      "/agent"
    ]
  }'
```

Known tags from `lovstudio/web:src/data/skills.ts`:

- `skills-index` — all catalog list pages.
- `skills-index:general` / `skills-index:dev` — the selected catalog.
- `skill:<id>` — SKILL.md and README detail.
- `skill-cases:<id>` — cases and articles.

## Verify the visible result

```bash
curl -fsS -o /tmp/lovstudio-skill-page.html \
  -w '%{http_code}\n' "https://lovstudio.ai/skills/<name>"
rg -n 'Version|<expected-version>|<expected-tagline>' \
  /tmp/lovstudio-skill-page.html
```

Completion gate:

- `/skills` lists the skill in the intended category.
- `/skills/<name>` returns HTTP 200.
- The visible detail version matches the released version.
- The live page contains the current tagline or another release-specific
  marker.

If any check fails, continue through catalog merge, cache revalidation, or site
deployment until the visible page is current.

## WorkBuddy distribution

When WorkBuddy is an enabled distribution target, complete the LovStudio source
release first, then build the platform archive from that exact source state:

```bash
python3 scripts/validate_skill.py .
python3 scripts/validate_skill.py . --target workbuddy
python3 scripts/build_workbuddy.py . --output-dir dist/workbuddy
shasum -a 256 dist/workbuddy.zip
unzip -l dist/workbuddy.zip
```

Follow `references/workbuddy.md`. Submit the generated ZIP together with its
source version, commit, checksum, validation output, and module count. A
manually assembled archive is not a release artifact.
