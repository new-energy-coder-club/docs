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

当前分为 6 个顶部 Tab，每个 Tab 下再按主题分组：

1. **首页** — 站点入口
2. **文档** — 重要文档、快速开始、新手上路、项目模块、机构 SIG、视觉与嵌入式、AI 工具、模板与规范
3. **竞赛** — 竞赛概览、CURC 2026
4. **社区** — 关于我们、社区与活动、治理与安全、核心团队、贡献指南
5. **Wiki** — Wiki 入门、Wiki 资源
6. **关于** — README、路线图、资源汇总

## 内容来源

- `wiki/` 目录为飞书 Wiki 导出快照，可通过 `.kimi/skills/feishu-to-nec-mdx/` Skill 从飞书导入/更新
- `competition/`、`curc26/` 下的历史文档正在逐步迁移到 Mintlify 导航

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
