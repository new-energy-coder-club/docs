# NEC 文档站点 — Agent 说明

## 项目类型

- 这是 NEC 新能源开发者社区的 **Mintlify** 文档站点
- 站点入口：`index.mdx`
- 站点配置：`docs.json`

## 本地开发

```bash
cd docs
mint dev
```

## 部署

推送到 `https://github.com/new-energy-coder-club/docs` 的 `main` 分支后，Mintlify 会自动部署到 https://docs.newenergycoder.club/。

## 文件规范

- 页面使用 `.mdx`（推荐）或 `.md`
- MDX 文件需包含 YAML frontmatter：
  ```mdx
  ---
  title: "页面标题"
  description: "页面描述"
  ---
  ```
- 新页面必须在 `docs.json` 的 `navigation` 中注册
- 图片放入 `images/` 目录，引用路径以 `/images/` 开头

## 导航结构

当前分为 7 个顶部 Tab，每个 Tab 下再按主题分组；分组内页面按「学习路径由浅入深」排序（2026-07 全站排序后固化）：

1. **首页** — 站点入口（`index`）
2. **文档**
   - 快速开始：`start-here/index` → `development`
   - 新手上路：通用新人指南 → CURC2027 onboarding → 夏令营 → first-good-issue
   - 10 日集训：`training/index` → day01–day05（按天数顺序）
   - 机构 SIG：机构概述 → 底盘（总览/全向轮/麦克纳姆）→ 培训教程（EK 培训/SolidWorks/Rhino）→ 子分组「设备与加工手册」（CNC 四篇 → Falcon2 → K1 打印机 → LumenPnP）→ 子分组「培训资料」（索引页 `training-resources` 置顶，再到设计方法论/减重/紧固件/铝管气动/设备与电机手册/提问与 Debug 软技能）
   - 视觉与嵌入式：视觉（Odin1 → MS200 雷达）→ 嵌入式（简介 → 环境搭建 → 控制 → 调试 → 电机控制系列）
   - AI 工具：IDE 类（Claude Code/Cursor/Windsurf）→ MCP/OpenClaw/飞书 CLI → 可行性研究 → Isaac Gym
   - 模板与规范：项目/竞赛/周报模板
3. **竞赛**
   - 竞赛概览：总览 → 子分组「ROBOCON备赛」（赛事介绍 → 2026 指南 → 新人指南 → 资料存档 → 资料包）→ 节能减排 → 智能汽车
   - CURC 2026：提案 `proposal` 置顶 → 机构 SIG（about/机械/电控/能力）→ 视觉 SIG → 运营 SIG
   - CURC 2027：总览 `index` 置顶 → 新人学习区 `onboarding` → 机构 SIG（机械+电控）→ 视觉 SIG（视觉+硬件）→ 运营 SIG；内容同步自 Gitee `feat/curc2027-onboarding` 分支 `competitions/CURC2027ROBOCON`
4. **社区**
   - 关于我们：关于 → 报名流程 → 加入合集 → NEC+ → Skill 分支 → 赞助
   - 社区与活动：社区 → A416 实验室 → 项目 → 导师 → Discord → 故事
   - 治理与安全：GOVERNANCE → CODE_OF_CONDUCT → SUPPORT → SECURITY
   - 核心团队：团队总览 → 维护者名单
   - 贡献指南：总览 → 规范 → 流程 → 代码风格 → Gitee 协作
5. **Wiki** — Wiki 总览、新人入门、社区与协作、培训与资源、规范与安全
6. **关于** — 路线图（`ROADMAP`）、资源汇总（`resource-index`）
7. **技能库** — Skill 分支 150 个 AI Coding Skills 的详情页（`skills/*.mdx`，由脚本从 `github/Skill` 分支批量生成）
   - 概览：`skills/index`（核心推荐 7 个前置 + 推荐 143 个按 12 大类的完整索引表）置顶
   - 核心推荐（NEC 精选）（7）：`nec-resource-publisher`、`nec-wechat-sync`、`pv-station-rating`、`pv-storage-bom`（仓库独家自研）+ `patent-application-cn`、`cit-thesis-writer`、`acad-paper-prompter`（学术方向社区精选）—— 导航与索引均前置展示
   - 12 个推荐分组（收录自 6 大平台）：飞书/Lark 办公套件（25）→ AI CLI 调用器（6）→ 前端 & 设计开发（14）→ 开发工程 & 工作流（17）→ 搜索 & 资讯聚合（8）→ 文档 & 办公文件（8）→ 集成 & 平台连接（14）→ 学术 & 论文（3）→ QClaw/OpenClaw 平台（15）→ 效率 & 头脑风暴（9）→ 社交 & 微信生态（7）→ TRAE 内置 & 独立工具（17）
   - 核心推荐技能同时从原分类（新能源 & 光伏、学术 & 论文等）移出，原「新能源 & 光伏」分组因移空而撤销；分组内技能按索引表固有顺序排列，每个技能只归一类

排序原则：新增页面时，索引/概述类页面置于分组首位，其余按学习路径由浅入深排列；修改导航结构后同步更新本节说明。

## 内容来源

- `wiki/` 目录为飞书 Wiki 导出快照，可通过 `.kimi/skills/feishu-to-nec-mdx/` Skill 从飞书导入/更新
- `competition/`、`curc26/` 下的历史文档正在逐步迁移到 Mintlify 导航

## 仓库分工（文档仓 vs 主代码仓）

社区有两个职责不同的仓，**互不合并、互不镜像**，2026-07-25 全量比对确认两边无内容一致的重叠文件：

| | 文档仓（本仓） | 主代码仓（资料仓） |
|---|---|---|
| 地址 | `github.com/new-energy-coder-club/docs` → https://docs.newenergycoder.club | `gitee.com/darrenpig/new_energy_coder_club` |
| 定位 | 发布态：面向读者的 Mintlify 文档站 | 工作态：原始资料与项目代码的存档仓 |
| 内容 | `.mdx` 页面 + frontmatter + `docs.json` 导航 | 历年赛事档案（`competitions/`）、项目代码与模型（`projects/`）、共享素材（`shared/`）、原始文档（`docs/`） |
| 大二进制 | **不入 git**，统一传 R2 CDN（`cdn.newenergycoder.club/files/...`）后链接 | 直接入库（PDF / STEP / zip / docx / 代码均可） |
| 分支 | 仅 `main`，推送即自动部署 | `master` 为主，另有 `SKill`、`feat/*-onboarding` 等工作分支 |

协作规则：

1. **不做仓间合并或整仓同步**——两仓结构与定位不同，允许各自独立演化
2. 内容流向是单向提炼：主代码仓沉淀原始材料 → 文档仓整理为带导航的发布页，大文件传 R2 后在页面中给 CDN 链接
3. 同名治理文件（GOVERNANCE / ROADMAP / SECURITY / SUPPORT / CODE_OF_CONDUCT 等）以**文档仓版本为准**对外发布，不回写主代码仓
4. 文档页引用主代码仓内容时，直接链接 Gitee 对应路径，不把其中的大二进制复制进本仓

## 持续集成

- `.github/workflows/docs-check.yml` 会在 `push` / `pull_request` 时自动运行
- 检查项包括：
  - `docs.json` JSON 合法性与推荐字段（`metadata`、`search`、`seo`）
  - 导航中的页面文件存在性
  - `.mdx` 文件包含非空 `title` 与 `description` 的 YAML frontmatter
  - Markdown / MDX 内部链接可解析，不含 `localhost` 与非 ASCII 路径
  - `robots.txt` 存在
  - 外部链接抽样健康检查（警告级别）
  - 未重新引入已删除的归档目录（`legacy/`、`api-reference/`、`essentials/`）
- 本地可手动执行：
  ```bash
  python tools/ci/check_docs.py
  ```

## 主题样式

- 自定义主题文件为根目录 `style.css`
- 已在 `docs.json` 中通过 `styles: ["style.css"]` 显式引用

## 注意事项

- 不要再引入 Sphinx / Read the Docs 配置
- 不要创建仅包含 toctree 的 `.rst` 索引文件
- 空菜单不要上线：新增导航项时必须确认目标页面存在且有实质内容
