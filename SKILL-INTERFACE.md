# NEC 文档维护 Skill 接口说明

本仓库内置了 `nec-docs-maintainer` Skill，用于封装 NEC Mintlify 文档站点的维护流程，方便 AI Agent 自动加载或人工复制安装。

## 位置

- **项目内 Skill（Kimi 自动加载）**: `.kimi/skills/nec-docs-maintainer/`
- **Gitee SKill 分支源版**: `https://gitee.com/darrenpig/new_energy_coder_club/tree/SKill/skills/nec-docs-maintainer/`

## AI 访问方式

### 方式一：自动加载（推荐）

Kimi Code CLI 进入本仓库工作区时，会自动加载 `.kimi/skills/nec-docs-maintainer/SKILL.md`。触发词包括：

- 维护 NEC 文档
- 修复文档死链
- 重构导航
- 新增 NEC 页面
- 部署文档站
- 运行 docs-check

### 方式二：复制到用户级 Skill 目录

如需在其他仓库或全局使用，可复制到用户 Skill 目录：

```bash
# Kimi 用户级 Skill 目录
mkdir -p ~/.kimi/skills
cp -r .kimi/skills/nec-docs-maintainer ~/.kimi/skills/

# 或通用 agents 目录
mkdir -p ~/.config/agents/skills
cp -r .kimi/skills/nec-docs-maintainer ~/.config/agents/skills/
```

### 方式三：从 Gitee 安装

```bash
git clone -b SKill https://gitee.com/darrenpig/new_energy_coder_club
cp -r new_energy_coder_club/skills/nec-docs-maintainer ~/.kimi/skills/
```

## Skill 内容

```
.kimi/skills/nec-docs-maintainer/
├── SKILL.md                           # 技能主文件
└── references/
    ├── project-structure.md           # 项目结构与关键文件
    └── ci-checks.md                   # CI 检查项与白名单
```

## 维护更新

当文档站点的工作流程、导航结构或 CI 规则发生变化时，请同步更新：

1. `.kimi/skills/nec-docs-maintainer/` 下的 SKILL.md 与 references
2. Gitee `SKill` 分支的 `skills/nec-docs-maintainer/` 目录
3. 本接口说明文件 `SKILL-INTERFACE.md`

保持三处一致，确保 AI 与人类协作者看到的是同一份维护规范。
