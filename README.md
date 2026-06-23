# NEC 社区文档站点

本目录包含 NEC (New Energy Coder) 新能源开发者社区的 [Mintlify](https://mintlify.com) 文档站点源码。

在线地址：**https://docs.newenergycoder.club/**

## 📁 目录结构

```
docs/
├── docs.json              # Mintlify 站点配置与导航
├── index.mdx              # 站点首页
├── favicon.svg            # 站点图标
├── logo/                  # 亮/暗主题 Logo
├── images/                # 图片资源
│
├── wiki/                  # 飞书 Wiki 导出文档
├── start-here/            # 新手上路
├── competitions/          # 竞赛文档
├── competition/           # 竞赛概览与经验（Mintlify 页面）
├── curc26/                # CURC 2026 赛季
├── projects/              # 开源项目文档（待补充）
├── community/             # 社区与贡献
├── learn/                 # 学习资源
├── contribute/            # 贡献标签与说明
├── nec-plus/              # NEC+ 付费会员
├── nec_quickstart/        # 快速开始
├── modules/               # 项目模块技术文档
├── mechanical/            # 机构设计
├── vision/                # 视觉识别
├── embedded-software/     # 嵌软开发
├── contributing/          # 贡献指南
├── templates/             # README 模板
└── tools/                 # 文档工具（如 feishu-import）
```

## 🚀 本地预览

### 安装 Mintlify CLI

```bash
npm install -g mintlify
```

### 启动本地服务

```bash
cd docs
mint dev
```

默认在 http://localhost:3000 预览。

## 🌐 部署

仓库已接入 Mintlify Git 集成。向 `main` 分支推送后自动部署到：

- 仓库：https://github.com/new-energy-coder-club/docs
- 在线站点：https://docs.newenergycoder.club/

## 📝 文档格式

本站使用 **MDX**（推荐）与 **Markdown** 两种格式：

- `.mdx` — Mintlify 原生格式，支持 React 组件与 YAML frontmatter
- `.md` — 普通 Markdown，可直接渲染

### 添加新页面

1. 在对应目录创建 `.mdx` 或 `.md` 文件。
2. 在 `docs.json` 的 `navigation.tabs[].groups[].pages` 中加入文件路径（不含扩展名）。

示例：

```json
{
  "group": "快速开始",
  "pages": ["quickstart", "development", "your-new-page"]
}
```

### 页面头部模板（MDX）

```mdx
---
title: "页面标题"
description: "页面描述"
---
```

## 🔁 飞书 Wiki 导入

仓库提供了 `tools/feishu-import/` 脚本，用于将 NEC 飞书 Wiki 顶层节点导入为 Markdown：

```bash
# 从父仓库进入工具目录
cd ../tools/feishu-import

# 导入顶层 Wiki 节点
python import_wiki_top_level.py \
  --source "https://scn0bdoc8zxg.feishu.cn/wiki/S10LwzVZdiWLwxkEnEqcTcmEn6e" \
  --out-dir ../../docs/wiki
```

脚本说明：
- `fetch_feishu_content.py`：修复 Windows 兼容性的 feishu-doc-webify 抓取脚本
- `import_wiki_top_level.py`：将飞书 Wiki 顶层节点转换为 Markdown 并导入 `docs/wiki/`

## 📚 参考资源

- [Mintlify 文档](https://www.mintlify.com/docs)
- [Mintlify 组件](https://www.mintlify.com/docs/content/components/frames)
- [MDX 文档](https://mdxjs.com/)

## 🤝 贡献

如需更新文档，请：

1. 修改相关 `.mdx` 或 `.md` 文件
2. 本地运行 `mint dev` 预览
3. 提交 PR 到主分支

详细的贡献指南请参考：[CONTRIBUTING.md](../CONTRIBUTING.md)
