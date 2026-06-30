# NEC 新能源开发者社区文档站

[![在线文档](https://img.shields.io/badge/docs-docs.newenergycoder.club-blue)](https://docs.newenergycoder.club/)
[![官网](https://img.shields.io/badge/官网-newenergycoder.club-green)](https://www.newenergycoder.club/)
[![Gitee](https://img.shields.io/badge/Gitee-new_energy_coder_club-red)](https://gitee.com/darrenpig/new_energy_coder_club)
[![GitHub](https://img.shields.io/badge/GitHub-new--energy--coder--club-black)](https://github.com/new-energy-coder-club/docs)

> 面向机器人竞赛与真实工程项目的开源工程社区文档站。沉淀 ROBOCON、RoboMaster、智能车等赛事的机械、嵌入式、机器视觉与运营经验。

## 在线访问

**https://docs.newenergycoder.club/**

推送代码到本仓库 `main` 分支后，[Mintlify](https://mintlify.com) 会自动构建并部署。

## 技术栈

- [Mintlify](https://mintlify.com) — 文档站点框架
- MDX — 页面内容
- Python — 文档健康检查脚本

## 本地开发

### 环境要求

- Node.js 18+
- Python 3.10+
- Git

### 安装依赖

```bash
npm install -g mintlify
```

### 启动预览

在项目根目录运行：

```bash
mint dev
```

本地服务器默认在 http://localhost:3000 启动，保存文件后自动热更新。

## 提交前检查

```bash
python tools/ci/check_docs.py
```

检查项包括 `docs.json` 合法性、导航页面存在性、MDX frontmatter 完整性、内部链接可解析性等。

## 项目结构

```
.
├── index.mdx                 # 站点首页
├── docs.json                 # Mintlify 站点配置与导航
├── style.css                 # 自定义主题样式
├── robots.txt                # 搜索引擎与 AI 爬虫指引
├── AGENTS.md                 # 给 AI Agent 的项目说明
├── images/                   # 图片资源
├── start-here/               # 快速开始与新手上路
├── modules/                  # 项目模块总览
├── mechanical/               # 机械设计专题
├── vision/                   # 机器视觉专题
├── embedded-software/        # 嵌入式软件专题
├── ai-tools/                 # AI 工具指南
├── competition/              # 竞赛概览
├── curc26/                   # CURC 2026 赛季文档
├── community/                # 社区介绍与治理
├── contributing/             # 贡献指南
├── wiki/                     # 飞书 Wiki 导出快照
└── tools/ci/                 # CI 检查脚本
```

## 贡献指南

1. 阅读 [贡献指南](/contributing/guidelines.mdx) 与 [工作流](/contributing/workflow.mdx)。
2. 创建或修改 `.mdx` 页面，确保包含 `title` 与 `description` 的 YAML frontmatter。
3. 在 `docs.json` 的 `navigation` 中注册新页面。
4. 运行 `python tools/ci/check_docs.py` 确认无错误。
5. 提交 PR 并等待 Review。

## 社区

- 官网：https://www.newenergycoder.club/
- Gitee 主仓库：https://gitee.com/darrenpig/new_energy_coder_club
- GitHub 文档仓库：https://github.com/new-energy-coder-club/docs
- ROBOCON 官网：https://www.cnrobocon.net/

## 许可证

本项目采用 [木兰宽松许可证第 2 版（Mulan PSL v2）](./LICENSE)。
