#!/usr/bin/env python3
"""Initialize and optionally install a portable local Skill Publisher Skill."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple


CONTENT_CLASSES = (
    "authored-prose",
    "microcopy",
    "verbatim",
    "deterministic-output",
)

SKILL_MD = """---
name: {name}
description: >
  {name}：把给定输入转成约定的交付结果，说明支持的输入、产出与边界。Use it to
  produce that result, e.g. "帮我……" / "create the output". 发布前替换为真实触发语。
license: MIT
compatibility: "Portable Agent Skills format. Python 3.8+ and PyYAML when scripts run."
metadata:
  author: skill-publisher
  version: "0.1.0"
  card_standard: skill-card/v1
  content_class: {content_class}
  tags:
    - {name}
---

# {title}

{name} 接收明确输入并产出约定结果。本文件是脚手架骨架：发布前把下方各节替换为真实
工作流与验收标准，并把 `cases/cases.json` 里的示例案例换成一次真实运行。

## Triggers

### Activate when

- 用户说“帮我用 {name} 处理……”并给出可执行的输入。
- The user asks to use {name} to create the stated output.
- 用户提交与本节输入类型一致的素材、数据或请求。

### Do not activate when

- 用户只是咨询概念、闲聊，或没有可执行的输入。
- 相邻任务属于其他能力时，明确说明应交给什么能力。

{user_profile_section}{kit_section}{skill_composition_section}{authorship_section}## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve skill root, dependencies, and runtime context

- Use `SKILL_DIR` if the environment provides it.
- Otherwise infer the installed skill directory from the current skill context.
- Verify every required local module, reference, script, and asset before work.
- If a required resource is missing, name its expected relative path and stop
  before producing a partial result.

When running scripts manually:

```bash
export SKILL_DIR="/path/to/{name}"
```

{user_profile_runtime}### Step 1: Understand the requested outcome

- Separate internal context from user-visible output.
- Confirm the input, intended audience, expected deliverable, and evidence gaps.
- Replace the scaffold case in `cases/cases.json` with one real run before
  release; the case must show input, prompt or brief, and output.

### Step 1.5: Analyze nearby Skills before implementation

- Inspect related local and installed Skills by routing contract and concrete
  input/output, not by filename alone.
- Record upstream, core, downstream, overlap, and not-composed decisions in
  `references/skill-composition.md`, then delete its scaffold marker line.
- Keep sibling Skills optional and artifact-based. When stages require hard
  coupling for one outcome, create a self-contained Kit instead.

### Step 2: Execute the workflow

Describe the executable steps here. Only deterministic operations need scripts.
Replace this paragraph with the real procedure and its acceptance checks.

### Step 3: Validate the deliverable

- Verify completeness, factual support, user-visible copy, and output paths.
- Report concrete files or results, plus any remaining evidence gaps.
- Run `python3 scripts/validate_skill.py . --strict` before any release.

## Dependencies

None beyond the runtime declared in `compatibility`.
"""

USER_PROFILE_SKILL_SECTION = """## User Profile (cross-session)

Every generated Skill is connected to the shared `user-profile/v1` contract in
`skill.yaml`. Read the shared user, brand, workspace, preferences, and this
Skill's `skills.<skill_id>` namespace at the start of every run. Keep the source
portable: resolved personal values belong in the shared profile, never here.

When the user directly states a durable preference or brand fact, persist it
through `scripts/profile_store.py` and report the saved profile path. Put
Skill-specific values under `records.<field>`; use `brand.<field>` or
`user.<field>` for shared values. Do not persist inferred secrets or credentials.
See `references/user-profile.md` for the complete contract.

"""

USER_PROFILE_RUNTIME = """Resolve `context.profile` on every invocation. The precedence is current request,
project context, Skill-specific profile records, shared preferences, shared
brand/user profile, then safe defaults. A direct user statement about a durable
preference or brand fact should be saved with `scripts/profile_store.py record`
using `--confirm`, followed by a concise saved-path report.

"""

SKILL_COMPOSITION_SECTION = """## Skill Group Composition

Read `references/skill-composition.md` before deciding whether to invoke or
extend any adjacent capability. The record distinguishes optional upstream and
downstream handoffs from embedded Kit modules. Do not silently depend on a
sibling Skill that is not shipped with this source.

"""

AUTHORSHIP_SKILL_SECTION = """## Authorship Integrity

This Skill creates authored prose, so read `references/authorship-integrity.md`
before drafting or revising. Build an authorship ledger from supplied evidence,
audit discourse before sentence polish, preserve counterevidence and unresolved
questions, and never invent firsthand experience, motives, quotations, numbers,
or causal links merely to make the text feel human.

"""

AUTHORSHIP_INTEGRITY_MD = """# Authorship Integrity Contract

Use this contract when `metadata.content_class` is `authored-prose`. It governs
essays, articles, reports, scripts, letters, and other prose where the writer's
reasoning and editorial choices are part of the deliverable.

## Authorship ledger

Before drafting, record:

- `source_question`: the real question or tension behind the piece;
- `author_positions`: claims explicitly supplied or approved by the user;
- `firsthand_evidence`: experiences, observations, decisions, and emotions that
  are safe to write in the first person;
- `editorial_decisions`: what to foreground, omit, defer, or leave unexplained;
- `counterevidence`: facts and interpretations that complicate the main claim;
- `open_questions`: uncertainty that should survive the draft;
- `preserve_verbatim`: quotations, transcripts, legal text, names, numbers, and
  identifiers that must not be paraphrased;
- `forbidden_inventions`: experiences, motives, facts, quotations, and causal
  links the Skill must not add.

## Discourse audit

Inspect the draft before surface polishing:

1. thesis provenance — trace each major claim to evidence or an explicit author
   decision;
2. causal compression — reject neat explanations that collapse a complex process
   without support;
3. counterevidence survival — preserve meaningful exceptions and alternatives;
4. closure pressure — do not resolve more than the evidence permits;
5. reader inference budget — leave room for readers to connect supported ideas;
6. structural asymmetry — let the material determine section size and order;
7. author decision trace — show why a fact, example, or boundary mattered.

## Boundaries

- Do not fabricate personal noise, false starts, typos, memories, or emotional
  confession to simulate humanity.
- Do not force every piece into conflict, reversal, open ending, or human-values
  uplift. Those are options only when the material supports them.
- Do not treat surface metrics or detector scores as authorship proof.
- For `verbatim`, preserve source text. For `microcopy`, optimize clarity and
  brand fit. For `deterministic-output`, validate correctness and completeness.
"""

KIT_SECTION = """## Skill Kit Modules

This repository is a self-contained Skill Kit. At Step 0, load and verify:

{module_lines}

`kit.yaml` is the machine-readable module and pipeline manifest. Every module
listed there must ship inside this repository.

"""

README_MD = """# {name}

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

脚手架说明：发布前把本行替换为这个 Skill 交付给用户的具体结果。

## 本地安装

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${{SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}}"
ln -s "$SKILL_SOURCE_DIR" \
  "$SKILL_SKILLS_INSTALL_DIR/{name}"
```

{configuration_section}## 使用

脚手架说明：发布前补两个真实示例，分别写明输入与输出。

## 原子组合

每个新 Skill 都带有 `references/skill-composition.md`。它记录已检查的相邻
Skills、可选的上游/下游交接、重叠处理，以及为何选择 Single Skill 或自包含
Skill Kit；外部 sibling Skill 不作为隐藏依赖。

## 可信度卡与用户案例

每个新 Skill 都必须随源代码提供：

- `skill-card.yaml` / `skill-card.md`：用途、负责人、依赖、风险、输出与维度地图。
- `cases/cases.json`：至少一个真实的 Input → Prompt → Output 案例。
- `pricing-card.yaml`：免费或付费都要写清价值锚点、交付边界和复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.8+
- PyYAML

## License

MIT
"""

SKILL_CARD_YAML = """
schema: skill-card/v1
scaffold: true
version: "0.1.0"
description: "Scaffold description: replace with the user-visible outcome in one concise paragraph."
owner:
  team: "unassigned"
  contact: "unassigned"
license:
  name: MIT
  terms: "MIT. Replace with any additional usage term a user must know."
  url: "../LICENSE"
use_case:
  audience: "Scaffold audience: replace with the real audience."
  scenario: "Scaffold scenario: replace with the real scenario."
  tasks:
    - "Scaffold task: replace with one real supported task."
deployment:
  geography: global
  environments:
    - local
requirements:
  credentials: "none"
  dependencies: []
  runtime:
    - "python3"
risks:
  - risk: "Scaffold risk: replace with one real failure or misuse mode."
    mitigation: "Scaffold mitigation: replace with the real mitigation."
references:
  - title: "Primary Skill instructions"
    path: "SKILL.md"
output:
  types:
    - "Scaffold output type: replace with the real output type."
  formats:
    - "Scaffold output format: replace with the real format."
  parameters:
    - "Scaffold parameter: replace with one real parameter."
  validation:
    - "Scaffold validation: replace with one real check."
  description: "Scaffold output description: replace before release."
ethical_considerations: "Scaffold boundary: replace with privacy, copyright, safety, or misuse limits."
dimensions:
  - id: correctness
    label: "Correctness"
    description: "Scaffold: does the output match the declared contract?"
    evidence: "Scaffold evidence: replace with the check that produced this answer."
    score: null
  - id: effectiveness
    label: "Effectiveness"
    description: "Scaffold: does the result solve the user task?"
    evidence: "Scaffold evidence: replace with the observed run that supports this."
    score: null
  - id: efficiency
    label: "Efficiency"
    description: "Scaffold: is the cost in steps, tokens, or time acceptable?"
    evidence: "Scaffold evidence: replace with the measured run that supports this."
    score: null
pricing:
  model: free
  currency: CNY
  list_price_cny: 0
  basis: "Scaffold basis: replace with why this Skill is free or priced."
  boundary: "Scaffold boundary: replace with what is included and excluded."
  review_trigger: "Scaffold review trigger: replace with the event that forces a review."
  confidence: internal
distribution:
  paid: []
  free:
    - github
    - website
"""

SKILL_CARD_MD = """
# Skill Card — {name}

scaffold: true

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source. Every section below ships as scaffold content; replace it with real
evidence and delete the `scaffold: true` line above.

## Description

Scaffold description: replace with the user-visible outcome.

## Owner

Unassigned. Replace with the maintaining team and contact.

## License / Terms

MIT. Replace with the license and any material usage term a user must know.

## Use Case

Scaffold use case: replace with the audience, supported input, and expected task.

## Deployment Geography

Global, running locally. Replace with the intended runtime scope.

## Requirements / Dependencies

Python 3.8+ and PyYAML when scripts run. Replace with the real credentials,
runtime, files, APIs, and dependencies.

## Known Risks and Mitigations

Scaffold risk: replace with the meaningful failure or misuse modes and how they
are mitigated.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)

## Skill Output

Scaffold output: replace with the output type, format, parameters, and
validation checks.

## Skill Version

0.1.0

## Ethical Considerations

Scaffold boundary: replace with privacy, copyright, safety, and attribution
limits.

## Trust evidence

### User Cases

See [`cases/cases.json`](cases/cases.json). Every case must show Input → Prompt
→ Output. The shipped case is a scaffold placeholder until a real run replaces
it.

### Dimension Map

The machine-readable card contains the dimensions, evidence, and score status.

### Pricing Basis

See [`pricing-card.yaml`](pricing-card.yaml). Free Skills still explain their
value, boundary, and review trigger.

### Distribution

Keep paid channels (`workbuddy`, `skillpay`) and free channels (`github`,
`website`) explicit. A planned or unavailable channel must not be described as
live.
"""

PRICING_CARD_YAML = """
schema: pricing-card/v1
scaffold: true
version: "0.1.0"
model: free
currency: CNY
list_price_cny: 0
value_anchor: "Scaffold value anchor: replace with the outcome a user gets without this Skill."
basis: "Scaffold basis: replace with why this Skill is free or priced."
boundary: "Scaffold boundary: replace with what is included and excluded."
review_trigger: "Scaffold review trigger: replace with the event that forces a review."
confidence: internal
"""

CASES_JSON = """
[
  {
    "type": "case",
    "scaffold": true,
    "title": "Scaffold case: replace with one real run",
    "description": "Placeholder record that keeps the trust bundle structurally valid. Replace it with a real run, including where the input came from and why the result mattered.",
    "input": {
      "items": ["Scaffold input: replace with the real input file, request, or starting state"]
    },
    "prompt": "Scaffold prompt: replace with the minimum prompt or brief that produced the result.",
    "output": {
      "items": ["Scaffold output: replace with the real output file, result, or decision"]
    }
  }
]
"""

CARD_STANDARD_REFERENCE_MD = """# Skill Card standard

`skill-card.yaml` follows the minimum release-record idea of NVIDIA Skill Cards:
description, owner, license/terms, use case, deployment, requirements,
risks/mitigations, references, output contract, version, and ethical
considerations. This standard adds evidence that helps a user decide whether the
Skill is credible:

1. A real user case with Input → Prompt → Output.
2. A dimension map with named evidence, not an unexplained score.
3. A pricing basis, including the free boundary and review trigger.
4. Explicit paid and free distribution states.

Never claim a case, score, channel, or price that has not been verified.
"""

README_CONFIGURATION = """## 用户 Profile（跨 session）

每个生成的 Skill 都会在 `skill.yaml` 中声明 `user-profile/v1`，并从共享
Profile 读取用户、品牌、工作区和本 Skill 的长期记录。用户直接说出的持久
偏好或品牌事实由 `scripts/profile_store.py` 写回 Profile；源代码保持可移植。

详见 [`references/user-profile.md`](references/user-profile.md)。

"""

SKILL_MANIFEST_YAML = """schema: skill-manifest/v1
id: {name}
version: "0.1.0"
runtime: skill-runtime/v1
context:
  profile:
    schema: user-profile/v1
    source: shared-profile
    read:
      - user
      - brand
      - workspace
      - preferences
      - skills.{name}
    persist:
      enabled: true
      namespace: skills.{name}
      records_path: skills.{name}.records
      write_policy: direct-user-statement
      atomic: true
    fields:
      - path: user.name
        aliases:
          - identity.name
        required: false
        question: 如果本次输出需要用户身份，请提供名称。
      - path: user.language
        required: false
        question: 希望使用哪种语言输出？
      - path: user.timezone
        required: false
        question: 需要使用哪个时区处理日期和时间？
      - path: brand.name
        aliases:
          - identity.name
        required: false
        question: 如果本次输出需要品牌身份，请提供品牌名称。
      - path: brand.site
        required: false
        question: 如果需要品牌官网，请提供地址。
      - path: brand.tone
        required: false
        question: 如果已有品牌语气或审美关键词，请提供它们。
  preferences:
    namespace: {namespace}
    fields:
      - path: user.language
        required: false
        question: 希望使用哪种语言输出？
      - path: user.timezone
        required: false
        question: 需要使用哪个时区处理日期和时间？
  interaction:
    ask_missing: true
    max_questions: 1
"""

KIT_YAML = """name: {name}
display_name: "{name}"
version: "0.1.0"
entrypoint: {name}
modules:
{module_entries}
pipelines:
  full:
{pipeline_entries}
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

Copyright (c) 2026 Skill Publisher

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

- Initial local Skill source.
"""

USER_PROFILE_MD = """# User Profile contract

Every Skill created by Skill Creator declares `user-profile/v1` in `skill.yaml`.
The contract connects independent sessions to one user-owned JSON Profile while
keeping the Skill source portable across users and brands.

## Shared shape

The host supplies the Profile through `SKILL_PROFILE_PATH` (or the runtime's
configured profile path). The stable shared scopes are:

- `user`: user identity, language, timezone, and other personal working defaults.
- `brand`: public brand facts, site, logo, tone, profile, and design guidance.
- `workspace`: project roots and output locations.
- `preferences`: shared preference values when the host stores them in the Profile.
- `skills.<skill_id>.profile`: Skill-specific defaults.
- `skills.<skill_id>.records`: durable decisions and preferences learned from
  direct user statements for this Skill.

The Profile may also use the runtime's canonical `identity` fields. Manifest
field aliases bridge `identity.*` and the portable `user.*` / `brand.*` names.

## Read on every run

1. Read the current request and project context.
2. Read the shared Profile and the `skills.<skill_id>` namespace.
3. Resolve values in this order: current request, project context, Skill records,
   shared preferences, shared user/brand Profile, safe defaults.
4. Keep `profile_scope` and field provenance available for the final result.

Do not copy resolved personal paths, brand values, or private records into the
committed Skill source.

## Persist directly stated values

When the user explicitly gives a value meant to survive later sessions, save it
immediately after the user statement and report the canonical path:

```bash
python3 scripts/profile_store.py record \\
  --skill-id example \\
  --path records.subtitle_level \\
  --value '\"cet4\"' \\
  --confirm
```

For shared facts, use `--path brand.<field>` or `--path user.<field>`. The
script writes JSON atomically, preserves unrelated Profile data, increments a
numeric Profile revision when present, and never echoes the stored value.

Inferred information, credentials, tokens, cookies, and secret-like fields stay
out of durable records. If the user has not stated that a value should persist,
keep it in the current request context.

## Read the connected context

```bash
python3 scripts/profile_store.py read \\
  --skill-id example \\
  --pretty
```

The result contains `user`, `brand`, `workspace`, `preferences`, `skill`, and
`records` scopes. A host using `skill-runtime/v1` also returns the same binding
as `profile_scope` and `profile_contract`.

## Compatibility

`--user-config` remains accepted by the Creator as a compatibility flag for old
invocations. The Profile contract is now always generated; users do not choose
an initialization mode.
"""

SKILL_COMPOSITION_MD = """
# Skill Group Composition

scaffold: true

This record ships as scaffold evidence. Inspect the nearby Skill group, replace
each section with the real finding, then delete the `scaffold: true` line above.

## Nearby Skills Inspected

None recorded yet. Inspect the local Skill source root and the installed Skill
catalog, then list each related Skill with its routing contract and why it is
relevant or not relevant.

## Atomic Handoffs

No handoff recorded yet. Record each upstream/core/downstream handoff as input
artifact, owner, output artifact, and acceptance boundary. State explicitly when
there is no handoff.

## Overlap Decisions

No overlap recorded yet. Explain any overlap that should be reused, extended, or
intentionally kept separate.

## Composition Decision

This scaffold starts as a Single Skill. Replace with the real decision and state
whether the source is a Single Skill or a self-contained Skill Kit and why.
External sibling Skills remain optional unless their module is embedded inside
this source.
"""


def _expand_path(value: str) -> Path:
    return Path(os.path.expandvars(value)).expanduser()


def _nested(data: dict, dotted: str) -> Optional[str]:
    current = data
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return str(current) if current else None


def _load_profile() -> Tuple[Path, dict]:
    configured = (
        os.environ.get("SKILL_PROFILE_PATH")
        or os.environ.get("SKILLS_PROFILE_PATH")
        or os.environ.get("LOVSTUDIO_SKILLS_PROFILE")
    )
    if configured:
        profile = _expand_path(configured)
    else:
        candidates = (
            Path.home() / ".skills" / "skills" / "profile.json",
            Path.home() / ".skill-publisher" / "skills" / "profile.json",
        )
        profile = next(
            (candidate for candidate in candidates if candidate.exists()),
            candidates[-1],
        )
    if not profile.exists():
        return profile, {}
    try:
        return profile, json.loads(profile.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON in {profile}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


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
    if os.environ.get("SKILL_SKILL_CREATOR_REPOS_ROOT"):
        return _expand_path(os.environ["SKILL_SKILL_CREATOR_REPOS_ROOT"])
    profile_value = _profile_first(
        profile,
        (
            "skill-publisher.skill_repos_root",
            "skills.repos_root",
            "workspace.skill_repos_root",
            "workspace.skills_root",
        ),
    )
    return _expand_path(profile_value) if profile_value else Path.cwd()


def resolve_install_dir(cli_path: str) -> Optional[Path]:
    if cli_path:
        return _expand_path(cli_path)
    if os.environ.get("SKILL_SKILLS_INSTALL_DIR"):
        return _expand_path(os.environ["SKILL_SKILLS_INSTALL_DIR"])
    _, profile = _load_profile()
    profile_value = _profile_first(
        profile,
        (
            "skills.install_dir",
            "skill-publisher.skills_install_dir",
            "workspace.skills_install_dir",
        ),
    )
    return _expand_path(profile_value) if profile_value else None


def link_source(source: Path, install_path: Path) -> str:
    """Link the source into the agent skills directory.

    Prefers a real symlink. Falls back to a Windows directory junction and then
    to a recursive copy, so hosts without symlink permission still end with a
    working local install instead of a half-created Skill.
    """

    try:
        install_path.symlink_to(source, target_is_directory=True)
        return "symlink"
    except (OSError, NotImplementedError, AttributeError):
        pass
    if os.name == "nt":
        try:
            import subprocess

            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(install_path), str(source)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode == 0 and install_path.is_dir():
                return "junction"
        except (OSError, subprocess.SubprocessError):
            pass
    shutil.copytree(source, install_path)
    return "copy"


def normalize_name(value: str) -> str:
    name = value
    if name.endswith("-skill"):
        name = name[: -len("-skill")]
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise ValueError(
            "skill name must use lowercase letters, numbers, and single hyphens only"
        )
    return name


def write_skill(
    path: Path,
    name: str,
    kit_section: str,
    user_config: bool = False,
    content_class: str = "deterministic-output",
) -> None:
    """Write a Skill instruction file with the always-on profile contract."""

    path.write_text(
        SKILL_MD.format(
            name=name,
            title=f"{name} — scaffold",
            kit_section=kit_section,
            user_profile_section=USER_PROFILE_SKILL_SECTION,
            user_profile_runtime=USER_PROFILE_RUNTIME,
            skill_composition_section=SKILL_COMPOSITION_SECTION,
            authorship_section=(
                AUTHORSHIP_SKILL_SECTION if content_class == "authored-prose" else ""
            ),
            content_class=content_class,
        ),
        encoding="utf-8",
    )


def write_manifest(path: Path, name: str) -> None:
    (path / "skill.yaml").write_text(
        SKILL_MANIFEST_YAML.format(name=name, namespace=name.replace("-", "_")),
        encoding="utf-8",
    )


def write_profile_reference(path: Path) -> None:
    (path / "references").mkdir(exist_ok=True)
    (path / "references" / "user-profile.md").write_text(
        USER_PROFILE_MD, encoding="utf-8"
    )


def write_composition_reference(path: Path) -> None:
    (path / "references").mkdir(exist_ok=True)
    (path / "references" / "skill-composition.md").write_text(
        SKILL_COMPOSITION_MD, encoding="utf-8"
    )


def write_authorship_reference(path: Path) -> None:
    (path / "references").mkdir(exist_ok=True)
    (path / "references" / "authorship-integrity.md").write_text(
        AUTHORSHIP_INTEGRITY_MD, encoding="utf-8"
    )


def copy_runtime_scripts(path: Path, script_root: Path) -> None:
    scripts_dir = path / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    for script_name in ("validate_skill.py", "profile_store.py"):
        shutil.copy2(script_root / script_name, scripts_dir / script_name)


def write_card_bundle(path: Path, name: str) -> None:
    """Create the evidence and pricing records required for a new Skill."""
    (path / "cases").mkdir(exist_ok=True)
    (path / "references").mkdir(exist_ok=True)
    (path / "skill-card.yaml").write_text(
        SKILL_CARD_YAML, encoding="utf-8"
    )
    (path / "skill-card.md").write_text(
        SKILL_CARD_MD.format(name=name), encoding="utf-8"
    )
    (path / "pricing-card.yaml").write_text(
        PRICING_CARD_YAML, encoding="utf-8"
    )
    (path / "cases" / "cases.json").write_text(
        CASES_JSON, encoding="utf-8"
    )
    (path / "references" / "skill-card-standard.md").write_text(
        CARD_STANDARD_REFERENCE_MD, encoding="utf-8"
    )


def render_kit(name: str, modules: list[str]) -> tuple[str, str]:
    module_lines = "\n".join(
        f"- `$SKILL_DIR/skills/{module}/SKILL.md` — `{module}`"
        for module in modules
    )
    module_entries = "\n".join(
        "  - id: {module}\n"
        "    skill: {module}\n"
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="Short name without the -skill suffix")
    parser.add_argument("--path", default="", help="Custom local source parent")
    parser.add_argument(
        "--install-dir",
        default="",
        help="Local agent skills directory; also resolves from env/profile",
    )
    parser.add_argument(
        "--user-config",
        action="store_true",
        help="Compatibility flag; the user-profile contract is always generated",
    )
    parser.add_argument(
        "--kit",
        action="store_true",
        help="Create a Skill Kit controller and embedded child modules",
    )
    parser.add_argument(
        "--with-module-cards",
        action="store_true",
        help="Also generate a trust bundle per embedded module (requires --kit)",
    )
    parser.add_argument(
        "--content-class",
        choices=CONTENT_CLASSES,
        default="deterministic-output",
        help="Classify normal output so the scaffold applies the correct quality contract",
    )
    parser.add_argument(
        "--authored-prose",
        action="store_true",
        help="Compatibility shortcut for --content-class authored-prose",
    )
    parser.add_argument(
        "--module",
        action="append",
        default=[],
        help="Embedded module short name; repeat for each module (requires --kit)",
    )
    parser.add_argument(
        "--module-content-class",
        action="append",
        default=[],
        metavar="MODULE=CLASS",
        help="Override one embedded module output class; repeat as needed",
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

    if args.authored_prose and args.content_class not in (
        "deterministic-output",
        "authored-prose",
    ):
        print("ERROR: --authored-prose conflicts with --content-class", file=sys.stderr)
        return 1
    content_class = "authored-prose" if args.authored_prose else args.content_class

    if args.module and not args.kit:
        print("ERROR: --module requires --kit", file=sys.stderr)
        return 1
    if args.module_content_class and not args.kit:
        print("ERROR: --module-content-class requires --kit", file=sys.stderr)
        return 1
    if args.with_module_cards and not args.kit:
        print("ERROR: --with-module-cards requires --kit", file=sys.stderr)
        return 1
    if args.kit and not modules:
        print("ERROR: --kit requires at least one --module", file=sys.stderr)
        return 1
    if len(set(modules)) != len(modules):
        print("ERROR: module names must be unique", file=sys.stderr)
        return 1
    if name in modules:
        print("ERROR: a module name must differ from the controller name", file=sys.stderr)
        return 1

    module_content_classes: dict[str, str] = {}
    for item in args.module_content_class:
        module_name, separator, module_class = item.partition("=")
        try:
            module_name = normalize_name(module_name)
        except ValueError as exc:
            print(f"ERROR: invalid module content class target: {exc}", file=sys.stderr)
            return 1
        if not separator or module_class not in CONTENT_CLASSES:
            print(
                "ERROR: --module-content-class must use MODULE="
                + "|".join(CONTENT_CLASSES),
                file=sys.stderr,
            )
            return 1
        if module_name not in modules:
            print(
                f"ERROR: module content class target is not declared: {module_name}",
                file=sys.stderr,
            )
            return 1
        if module_name in module_content_classes:
            print(
                f"ERROR: duplicate module content class target: {module_name}",
                file=sys.stderr,
            )
            return 1
        module_content_classes[module_name] = module_class

    base = resolve_base(args.path)
    skill_dir = base / f"{name}-skill"
    install_dir = resolve_install_dir(args.install_dir)
    install_path = install_dir / f"{name}" if install_dir else None

    if skill_dir.exists() or skill_dir.is_symlink():
        print(f"ERROR: source already exists: {skill_dir}", file=sys.stderr)
        return 1
    if install_path and (install_path.exists() or install_path.is_symlink()):
        print(f"ERROR: install target already exists: {install_path}", file=sys.stderr)
        return 1

    base.mkdir(parents=True, exist_ok=True)
    skill_dir.mkdir()
    (skill_dir / "scripts").mkdir()

    kit_section = ""
    if args.kit:
        kit_section, kit_text = render_kit(name, modules)
        (skill_dir / "kit.yaml").write_text(kit_text, encoding="utf-8")
        for module in modules:
            module_dir = skill_dir / "skills" / module
            module_dir.mkdir(parents=True)
            module_content_class = module_content_classes.get(module, content_class)
            write_skill(
                module_dir / "SKILL.md",
                module,
                "",
                args.user_config,
                module_content_class,
            )
            if args.with_module_cards:
                write_card_bundle(module_dir, module)
            write_manifest(module_dir, module)
            write_profile_reference(module_dir)
            write_composition_reference(module_dir)
            if module_content_class == "authored-prose":
                write_authorship_reference(module_dir)

    write_skill(
        skill_dir / "SKILL.md",
        name,
        kit_section,
        args.user_config,
        content_class,
    )
    write_card_bundle(skill_dir, name)
    write_manifest(skill_dir, name)
    write_profile_reference(skill_dir)
    write_composition_reference(skill_dir)
    if content_class == "authored-prose":
        write_authorship_reference(skill_dir)
    (skill_dir / "README.md").write_text(
        README_MD.format(
            name=name,
            configuration_section=README_CONFIGURATION,
        ),
        encoding="utf-8",
    )
    (skill_dir / ".gitignore").write_text(GITIGNORE, encoding="utf-8")
    (skill_dir / "LICENSE").write_text(LICENSE_MD, encoding="utf-8")
    (skill_dir / "CHANGELOG.md").write_text(CHANGELOG_MD, encoding="utf-8")

    script_root = Path(__file__).resolve().parent
    copy_runtime_scripts(skill_dir, script_root)
    for module in modules:
        copy_runtime_scripts(skill_dir / "skills" / module, script_root)

    link_mode = "none"
    if install_path:
        install_dir.mkdir(parents=True, exist_ok=True)
        link_mode = link_source(skill_dir.resolve(), install_path)

    kind = "Skill Kit" if args.kit else "Skill"
    print(f"created={skill_dir.resolve()}")
    print(f"kind={kind}")
    print("profile_contract=user-profile/v1")
    print("composition_record=references/skill-composition.md")
    print(f"content_class={content_class}")
    for module in modules:
        print(
            f"module_content_class.{module}="
            f"{module_content_classes.get(module, content_class)}"
        )
    print(f"module_cards={'per-module' if args.with_module_cards else 'controller-only' if args.kit else 'not-applicable'}")
    print(f"user_config={'compatibility-flag' if args.user_config else 'always-on'}")
    print(f"link_mode={link_mode}")
    print(f"installed={install_path if install_path else 'pending'}")
    if install_path:
        print(f"install_target={install_path.resolve()}")
    print("validation=python3 scripts/validate_skill.py .")
    print("release_gate=python3 scripts/validate_skill.py . --strict")
    if not install_path:
        print("next=resolve a local agent skills directory and install the source")
    else:
        print("next=replace placeholders, validate, and exercise trigger routing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
