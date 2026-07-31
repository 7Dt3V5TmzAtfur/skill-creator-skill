---
name: lovstudio-skill-creator
description: >
  创建可发布的 LovStudio Skill 或自包含 Skill Kit，自动生成触发规则、标准 YAML、
  依赖校验与腾讯 WorkBuddy 发行包。适用于“创建 skill”“生成 Skill Kit”
  “scaffold skill”或“适配 WorkBuddy”等请求。
license: MIT
metadata:
  author: lovstudio
  version: "3.0.0"
  tags:
    - skill-creator
    - scaffold
    - workbuddy
    - skill-kit
  compatibility: "Python 3.8+, PyYAML, git, and gh CLI."
  dependencies: []
---

# lovstudio-skill-creator

Scaffold every new lovstudio skill as an **independent GitHub repo** under
`lovstudio/{name}-skill`. `lovstudio/dev-skills` is a generated distribution
bundle: its `skills/{name}/` directories mirror tagged releases and must not be
edited as source.

## Triggers

### Activate when

- 用户要“创建 skill”“封装成 skill”“生成 Skill Kit”或优化 Skill 生成机制。
- The user asks to scaffold, package, validate, or publish an Agent Skill.
- 用户要把 Skill 或 Skill Kit 适配到腾讯 WorkBuddy。

### Do not activate when

- 用户只是调用一个现有 Skill 完成业务任务，而不是创建或维护 Skill 本身。

## Architecture

```
<configured workspace>/
├── lovstudio-general-skills/     ← general skills index (lovstudio/general-skills repo)
│   ├── skills.yaml                ← machine-readable manifest (paid flag lives here)
│   └── README.md                  ← human-readable catalog
├── lovstudio-dev-skills/          ← generated aggregate for meta/dev skills
│   ├── skills.yaml
│   ├── .claude-plugin/marketplace.json
│   └── skills/{name}/             ← mirrors the latest independent release
│       ├── SKILL.md
│       ├── README.md
│       ├── scripts/
│       └── references/
├── skills/                        ← independent per-skill source repos
│   └── {name}-skill/
│       ├── SKILL.md
│       ├── README.md
│       ├── CHANGELOG.md           ← managed by skill-optimizer
│       ├── kit.yaml                ← optional, for a self-contained Skill Kit
│       ├── scripts/               ← standalone Python CLI scripts
│       ├── skills/                 ← embedded kit modules
│       ├── workbuddy/              ← optional platform distribution metadata
│       └── references/            ← optional progressive-disclosure docs
└── ...

<agent skills dir>/lovstudio-{name}  ← install or symlink to the source checkout
```

Key facts:
- Default GitHub repo name: `lovstudio/{name}-skill` (with `-skill` suffix)
- Default local source root: `LOVSTUDIO_SKILL_CREATOR_REPOS_ROOT`, profile
  `lovstudio.skill_repos_root`, or the current directory.
- General skills checkout path: configured by the maintainer's local checkout.
- Dev-skills catalog entries point to the independent `lovstudio/{name}-skill`
  repo. Its synchronization workflow mirrors the latest GitHub Release.
- Agent runtimes read an installed directory named `lovstudio-{name}/`.
- Frontmatter `name`: `lovstudio-{name}` (Agent Skills-compatible). Legacy
  namespace-style names are kept only for older skills and should not be copied
  into new templates.
- Source frontmatter uses only Agent Skills-compatible top-level fields.
  Compatibility and dependency declarations live under `metadata`.
- A required dependency must be embedded in a Skill Kit before a WorkBuddy
  release. `kit.yaml` is the module/path/pipeline contract.
- WorkBuddy-only fields (`version`, `author`, `source_type`, and a source
  locator) are injected into the distribution copy, not the source SKILL.md.
- `paid: true/false` lives **only** in `lovstudio-general-skills/skills.yaml`, never in SKILL.md
- User-specific paths, brand profiles, design guides, and output directories
  must be initialized through explicit CLI flags, environment variables, or
  `~/.lovstudio/skills/profile.json`. Do not hard-code personal workspace
  paths in reusable workflows.

## Skill Creation Process

### Step 1: Understand the Skill

Ask the user what the skill should do. Use `AskUserQuestion` — one question at
a time, in the order below. **Do not skip or reorder.** The commercial model
decides the architecture, so it has to come before any implementation question.

**Source repository invariant — do not ask:** every skill source lives in its
own `lovstudio/{name}-skill` repository. Never ask the user to choose a source
repository or scaffold target. Catalog and bundle registration are downstream
distribution decisions inferred from category and commercial model.

**Required question order:**

#### Q1. Commercial / protection model — ALWAYS ask first

Even for "obvious" simple skills, ask. Users may have future monetization plans
you can't infer from the initial request.

> 这个 skill 的分发定位?
>
> 1. **Free (public)** — 任何人 git clone 就能用。适合引流、通用工具、开源贡献。
> 2. **Paid, 普通 IP** — 核心逻辑是流程/模板/prompt 编排,用户 grep 出来不心疼。用加密分发 + license 鉴权。
> 3. **Paid, 敏感 IP** — 含算法参数/业务规则/调好的 prompt/API 密钥,用户反编译会心疼。用 cloud-split:核心逻辑放云端,本地只有瘦客户端。
>
> 提示:不确定 → 选 2。未来升级到 3 比降级容易。

这个答案决定后续流程分支:
- 选 1 → 走标准公开 repo 流程
- 选 2 → 走 encrypted skill 流程(README 里坦诚说明 "加密 = 鉴权闸门,不保证反提取")
- 选 3 → **停下来读 `references/cloud-split.md`**,然后走 cloud-split 流程

#### Q2. Problem & shape
- 解决什么问题?输入 → 输出是什么?
- 2-3 个具体使用示例
- 触发短语(中文 + English)

#### Q2.5. Public/protected decomposition — mandatory

Before creating files, show:

- **Public layer**: conversation flow, input parsing, output rendering, errors.
- **Protected layer**: algorithms, thresholds, rules, prompts, keys, or data;
  explicitly say “none” when empty.

Free accepts either shape. Encrypted is suitable for paid workflows whose
plaintext is not sensitive. Cloud-split requires a substantive protected layer;
read `references/cloud-split.md` for its full consistency and preflight rules.

For paid skills, name the capability domain instead of narrating the logic:
prefer `text-scorer` over `detect-viral-headline`, and `score` over
`check_if_headline_is_viral`.

#### Q3. Implementation type
- 纯指令 SKILL.md,还是需要 Python CLI 脚本?
- (如果 Q1 选了 3:这一问跳过。cloud-split 的"实现"就是云端 handler,不是本地脚本。)

Also decide the composition:

- **Single Skill** — one focused workflow.
- **Skill Kit** — a controller plus two or more embedded modules and named
  pipelines. List the modules and their order before scaffolding.

For a Skill Kit, use `--kit` with one `--module` per embedded module. Do not
leave required modules as external sibling paths.

#### Q4. Distribution target

Ask where the finished Skill will be distributed:

1. **LovStudio source/catalog only** — standard source repository.
2. **LovStudio + Tencent WorkBuddy** — add platform metadata, CI, a market icon,
   self-contained ZIP building, and Tencent review gates.

If WorkBuddy is selected, read `references/workbuddy.md` completely before
scaffolding. Use `--distribution workbuddy`; never hand-assemble the ZIP.

#### Q5. User initialization layer — mandatory for reusable skills

Ask whether the skill needs user-specific workspace, output, identity, brand,
or design-guide settings. If yes, design the initialization layer before
writing scripts:

> 这个 skill 是否需要读取用户自己的工作区、品牌资料、设计规范或输出目录?
>
> 1. **No user config** — 只处理当前输入文件/当前目录。
> 2. **User profile** — 需要用户初始化自己的 workspace/brand/output。
> 3. **LovStudio internal only** — 明确只服务 Mark/LovStudio 私有工作区。

Rules:
- Option 1: no absolute user paths in SKILL.md or scripts.
- Option 2: follow `references/user-config.md`; use CLI flags > env vars >
  shared profile > safe defaults > ask once.
- Option 3: mark `metadata.compatibility` and README as author-only, and keep all
  LovStudio paths in one configuration section instead of scattering them.

### Step 2: Plan Contents

Analyze the examples and identify:

1. **Scripts** — deterministic operations → `scripts/`
2. **References** — domain knowledge Claude needs while working → `references/`
3. **Assets** — files used in output (templates, fonts, etc.) → `assets/`
4. **Modules** — independently triggerable workflows → embedded `skills/`
5. **Distribution metadata** — platform-specific fields → `workbuddy/`

Rules:
- Python scripts must be **standalone single-file CLIs** with `argparse`
- No package structure, no `setup.py`, no `__init__.py`
- CJK text handling is a core concern if the skill deals with documents
- Any user-specific path, brand asset, design guide, or output root needs a
  configuration plan. Read `references/user-config.md` and include
  `references/user-config.md` in the scaffold for public/reusable skills.

### Step 3: Initialize

Run the init script. Independent repo is the default:

```bash
python3 "$SKILL_DIR/scripts/init_skill.py" <name>
```

For a WorkBuddy-ready Skill Kit:

```bash
python3 "$SKILL_DIR/scripts/init_skill.py" <name> \
  --kit \
  --module <module-a> \
  --module <module-b> \
  --distribution workbuddy
```

The repository includes source validation in every mode. The WorkBuddy mode
also generates `workbuddy/connector-meta.json`, `workbuddy/icon.svg`, a
platform CI workflow, and the self-contained distribution builder.

Independent repo creates `<configured repos root>/{name}-skill/` with:

```
{name}-skill/
├── SKILL.md          ← frontmatter + TODO workflow
├── README.md         ← human-readable docs with version badge
├── scripts/
│   └── validate_skill.py
├── kit.yaml          ← only in Skill Kit mode
├── skills/           ← embedded modules in Skill Kit mode
└── workbuddy/        ← only with --distribution workbuddy
```

Pass `--paid` if this is a paid skill (adjusts README + metadata hints).

**If Q1 chose cloud-split (tier 3)**: after running init_skill.py, don't put
your real logic in `scripts/`. Instead:
1. Read `references/cloud-split.md` end-to-end before writing any code
   **(this is not optional — the rules for non-leaky payloads are there, not here)**
2. **Start from `threshold-check` as the reference pattern**, NOT `paid-add`.
   `paid-add` is an architecture demo with an intentionally leaky payload
   (for teaching). Copying its return shape into a real skill defeats the
   whole point of cloud-split.
3. Write the handler in the configured web repo's `supabase/functions/skill_call/handlers/<name>.ts`
   — return a minimal symbolic payload (`{verdict: "A" | "B"}` style), not
   descriptive strings or narrative `display` fields
4. Write the thin SKILL.md per the `threshold-check` template — rendering
   via a **symbol → text table**, never via a computed algorithm
5. **MANDATORY pre-flight audit** — before registering the handler in the
   dispatcher, before deploying, before telling the user "done":
   run the checklist in `references/cloud-split.md` → "MANDATORY pre-flight
   audit" section. Report each item's result to the user. If any item
   fails, rewrite before moving on.
6. Skip the normal Step 4 "write scripts" — there usually aren't any for
   cloud-split skills (unless you need client-side rendering of server output)

**Why the audit is mandatory**: a real incident during skill-creator
development produced a cloud-split skill whose handler returned
`{score, verdict: "below", display: "2+6=8 (below 10)"}`. Architecture was
correct; protection was zero. The audit catches this class of bug before
it ships.

### Step 4: Implement

1. **Write scripts** in `scripts/` — test by running directly
2. **Write SKILL.md** — instructions for AI assistants:
   - Frontmatter `description` is the trigger mechanism — cover what + when +
     concrete trigger phrases (中文 + English)
   - Body contains workflow steps, CLI reference, field mappings
   - Use `AskUserQuestion` for interactive prompts before running scripts
   - Add a user configuration section when the workflow touches paths,
     personal data, brand assets, or workspace conventions
   - Never assume personal workspace paths or a fixed agent runtime path in
     reusable workflow steps
   - Keep SKILL.md under 500 lines; split to `references/` if longer
   - Use standard YAML; source top-level keys are limited to `name`,
     `description`, `license`, `allowed-tools`, and `metadata`
   - Keep descriptions between 50 and 200 characters
   - Add `## Triggers`, activation phrases, and explicit non-trigger conditions
   - Put compatibility and dependencies under `metadata`
3. **Write README.md** — docs for humans on GitHub:
   - Version badge (source of truth for version)
   - Install command using the user's chosen agent skills directory
   - Dependencies
   - Usage examples, options table
   - ASCII diagrams if useful

See `references/templates.md` for SKILL.md / README.md templates.
See `references/user-config.md` for the portable profile/env contract.
See `references/skill-standard.md` for the current LovStudio skill standard.

### Step 4.5: Validate and package

Every source repository:

```bash
python3 scripts/validate_skill.py .
```

WorkBuddy distributions:

```bash
python3 scripts/validate_skill.py . --target workbuddy
python3 scripts/build_workbuddy.py . --output-dir dist/workbuddy
```

The WorkBuddy build must fail when a module, local reference, case image,
source locator, trigger section, or required description is missing. It must
also reject private absolute paths, unresolved TODOs, `__pycache__`, and
compiled Python artifacts.

### Step 5: Publish

Always publish the skill's own repository first. Then infer distribution:

- Register general, public-facing, and paid skills in
  `lovstudio/general-skills`.
- Free Meta / Dev Tools skills may additionally be registered in
  `lovstudio/dev-skills`; its checked-in skill directory is a generated mirror
  of the independent release.
- Do not ask the user where the source should live.
- For WorkBuddy, submit only the ZIP emitted by `build_workbuddy.py`. Keep
  source and platform frontmatter separate. For kits, the builder also emits
  independently installable controller/module ZIPs so users can combine one or
  more capabilities.

### Single Source Repository

#### 5a. Initialize & push the skill's own repo

```bash
cd <configured-repos-root>/<name>-skill
git init
git add -A
git commit -m "feat: initial release of <name> skill"

# Free skill (public):
gh repo create lovstudio/<name>-skill --public --source=. --push

# Paid skill (private):
gh repo create lovstudio/<name>-skill --private --source=. --push
```

#### 5b. Register in the general-skills index

Edit the configured `lovstudio-general-skills/skills.yaml` — append under the right
category (category order in the yaml determines display order on the website):

```yaml
  - name: <name>
    repo: lovstudio/<name>-skill
    paid: false                         # or true for paid skills
    category: "<Category>"              # must match an existing category heading
    version: "0.1.0"
    description: "<One-line description matching SKILL.md tagline>"
```

Also add a row to the configured `lovstudio-general-skills/README.md` under the matching
category section. Then PR against `lovstudio/general-skills`:

```bash
cd <general-skills-checkout>
git checkout -b add/<name>
git add skills.yaml README.md
git commit -m "add: <name> skill"
git push -u origin HEAD
gh pr create --fill
```

#### 5c. Install for local availability

Make the skill immediately usable by installing or symlinking the source
checkout into the user's agent skills directory as `lovstudio-<name>`.

#### 5d. Synchronize to lovstudio.ai/skills (MANDATORY)

Publishing is incomplete until the skill is visible at
`https://lovstudio.ai/skills/<name>`. After the catalog change reaches `main`,
read `references/publishing.md` and run its cache-revalidation and live
verification workflow.

Do not report the skill as published until `/skills` lists it,
`/skills/<name>` returns HTTP 200, and the visible version and content match
the release.

### Dev-Skills Distribution Mirror

For a free Meta / Dev Tools skill, register its independent source in the
configured `lovstudio-dev-skills/skills.yaml`:

Edit the configured `lovstudio-dev-skills/skills.yaml`:

```yaml
- name: <name>
  repo: lovstudio/<name>-skill
  name_zh: <中文名>
  paid: false
  category: "Dev Tools"                 # or "Meta"
  version: "0.1.0"
  description: "<Agent-facing trigger description>"
  tagline_en: "<Human-facing English tagline>"
  tagline_zh: "<Human-facing Chinese tagline>"
```

Also update `.claude-plugin/marketplace.json` so the correct plugin includes
`"./skills/<name>"`, and add the repo to `independent-skills.json`. The mirror
directory is populated from the latest release by
`scripts/sync-independent-skills.py`; do not edit it manually.
- Meta skills → `plugins[].name == "meta"`
- Dev tooling → `plugins[].name == "dev-tools"`

Then render the READMEs:

```bash
GITHUB_TOKEN="$(gh auth token)" python3 scripts/sync-independent-skills.py sync
python3 scripts/render-readme.py
```

#### Install for local availability

Install or symlink the bundled skill directory into the user's agent skills
directory as `lovstudio-<name>`.

#### Commit and push the aggregate metadata

```bash
git add independent-skills.json skills.yaml README.md README.en.md .claude-plugin/marketplace.json skills/<name>
git commit -m "chore(skills): mirror <name> release"
git push -u origin HEAD
gh pr create --fill
```

Do not register dev-skills-only skills in the general-skills index
unless the user explicitly asks for the main Lovstudio skills index to list the
bundle entry.

### Step 6: Test & Iterate

1. In a new conversation, invoke `lovstudio-<name>` or a documented trigger phrase — confirm it triggers
2. Invoke at least one documented non-trigger request — confirm it does not hijack the task
3. For kits, exercise every module and at least one full pipeline
4. Rebuild the WorkBuddy ZIP from a clean checkout and validate the package
5. Notice struggles → edit SKILL.md / scripts in the source repo
6. Commit, tag, and push in the independent source repo; aggregate mirrors are
   updated from releases

## Design Patterns

### Interactive Pre-Execution (MANDATORY for generation/conversion skills)

```markdown
**IMPORTANT: Use `AskUserQuestion` to collect options BEFORE running.**

Use `AskUserQuestion` with the following template:
[options list]

### Mapping User Choices to CLI Args
[table mapping choices to --flags]
```

### Progressive Disclosure

Keep SKILL.md lean. Split to references when:
- Multiple themes/variants → `references/themes.md`
- Complex API docs → `references/api.md`
- Large examples → `references/examples.md`

Reference from SKILL.md: "For theme details, see `references/themes.md`"

### Context-Aware Pre-Fill

For skills that fill or generate content:
1. Check user memory and conversation context first
2. Pre-fill what you can
3. Only ask for fields you truly don't know

## What NOT to Include

- `INSTALLATION_GUIDE.md` — clutter; install instructions go in README.md
- Test files — scripts are tested by running, not with test frameworks
- `__pycache__/`, `*.pyc`, `.DS_Store` — add to `.gitignore`
- `paid` field in frontmatter — it lives only in `lovstudio-general-skills/skills.yaml`
- `compatibility`, `depends_on`, `version`, `author`, or WorkBuddy source fields
  as top-level source frontmatter keys
- External sibling modules in a release ZIP
- Hard-coded personal workspace paths or private LovStudio brand files in
  reusable workflows

## Migration Notes

For historical repo-layout migrations, read `references/migration.md`.
