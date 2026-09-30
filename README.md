# Skill 工坊 · Skill Studio

![Version](https://img.shields.io/badge/version-4.7.0-CC785C)

## Skill 群组原子组合

每次生成或迭代 Skill 前，先分析已有 Skills 的实际输入/输出合同，记录上游、核心、下游、重叠与不组合决策。新源默认携带 `references/skill-composition.md`；外部 sibling Skill 只作为可选交接，硬依赖必须嵌入为自包含 Kit 模块。

创建、验证并安装本地 Skill Publisher Skill 或自包含 Skill Kit。它会根据产品需求自动判断实现形态、Single/Kit 结构，并为每个新 Skill 自动绑定跨 session 的用户 Profile。

Creator 现在还会先区分 `authored-prose`、`microcopy`、`verbatim` 与
`deterministic-output`。文章、报告、脚本等作者性文本会自动得到作者性账本、
篇章审计与禁止伪造边界，不再只靠表层“去 AI 味”规则。

远程仓库、目录市场、平台发行包与上传验收由独立的 `skill-publisher` 负责。

## 安装

把本目录放到本地 Skill 源根目录，再链接到 Agent Skills 目录：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" "$SKILL_SKILLS_INSTALL_DIR/skill-creator"
```

Windows 等无 symlink 权限的环境会自动降级为目录联接（junction）或复制，
脚本会打印实际采用的链接方式。

## 创建本地 Skill

旧 slash command 也可迁移：先批量盘点，再按实际功能合并别名、升级已有真源，
或生成独立迁移工作区。迁移包括参数、工具、路径、授权边界、Profile 和真实验收，
不依赖 Claude Code 的命令插值。详见 [迁移流程](references/slash-command-migration.md)。

```bash
python3 "$SKILL_DIR/scripts/migrate_command.py" inventory \
  --command-root "$COMMAND_ROOT" --source-root "$SKILL_SOURCE_ROOT"
python3 "$SKILL_DIR/scripts/migrate_command.py" prepare "$COMMAND_FILE" \
  --name better-github-desc --content-class microcopy --output "$MIGRATION_WORK_AREA"
```

准备命令保留原文与摘要，拒绝覆盖已有工作区，不安装未完成的候选 Skill。
官网同步由 `skill-publisher` 接收已通过校验的真源并完成上线与安装回读。

```bash
python3 "$SKILL_DIR/scripts/init_skill.py" wcx \
  --content-class deterministic-output \
  --install-dir "$SKILL_SKILLS_INSTALL_DIR"
```

作者性文本：

```bash
python3 "$SKILL_DIR/scripts/init_skill.py" article-tool \
  --content-class authored-prose \
  --install-dir "$SKILL_SKILLS_INSTALL_DIR"
```

包含可独立调用阶段时，由代理自动创建 Skill Kit：

```bash
python3 "$SKILL_DIR/scripts/init_skill.py" bp \
  --kit \
  --module bp-outline \
  --module bp-deck \
  --module bp-polish \
  --install-dir "$SKILL_SKILLS_INSTALL_DIR"
```

混合 Kit 可以按模块覆盖，例如：

```bash
python3 "$SKILL_DIR/scripts/init_skill.py" publishing \
  --kit --module research --module draft \
  --module-content-class draft=authored-prose \
  --install-dir "$SKILL_SKILLS_INSTALL_DIR"
```

每个创建结果都会生成 `skill.yaml`、`references/user-profile.md` 和
`scripts/profile_store.py`。Profile 读取用户与品牌共享信息，用户直接说出的
长期偏好写入 `skills.<skill_id>.records`；旧命令中的 `--user-config` 仍可传入，
但只是兼容参数。

## 本地交付边界

Creator 的完成标准是：

1. 本地源码生成完成。
2. `python3 scripts/validate_skill.py .` 通过（脚手架证据只产生 warning）。
3. Skill 已链接到本地 Agent Skills 目录；无 symlink 权限时自动降级为
   junction 或复制，并打印实际链接方式。
4. 触发、非触发以及 Kit 流水线完成基本验收。
5. 发布前 `python3 scripts/validate_skill.py . --strict` 通过：用户案例、
   维度地图、定价依据和分发状态已替换为真实证据。

发布到 Skill Publisher、WorkBuddy 或其他平台时，使用 `skill-publisher`。

## 依赖

- Python 3.8+
- PyYAML
- Git（仅在需要本地版本历史时使用）

## Skill Card 标准

每次创建都会同时生成 `skill-card.yaml`、`skill-card.md`、
`cases/cases.json` 和 `pricing-card.yaml`，内容是可过检的脚手架证据并带
`scaffold: true` 标记。案例必须明确 Input → Prompt → Output；维度必须带
证据；免费 Skill 也要写清价值与使用边界。发布前替换这些记录并删除标记，
`--strict` 会把未替换的记录判为错误。

## 脚手架完成度

新建 Skill 默认即可通过本地校验：

```bash
python3 scripts/validate_skill.py .            # 通过，列出待替换的脚手架记录
python3 scripts/validate_skill.py . --strict   # 发布门禁，脚手架记录判为错误
```

Skill Kit 默认只在控制器层生成一套信任包，模块继承它；模块需要独立发布时
再加 `--with-module-cards`。

## License

MIT
