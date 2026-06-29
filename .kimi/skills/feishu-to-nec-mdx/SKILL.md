---
name: feishu-to-nec-mdx
description: 将飞书文档或 Wiki 知识库转化为 NEC Mintlify 文档站的 .mdx 资料。用于把飞书内容沉淀到 docs.newenergycoder.club，包含 frontmatter 生成、图片本地化、docs.json 导航注册与 CI 检查。触发词：飞书转 mdx、飞书转 NEC 文档、feishu to mdx、导入飞书到文档站、飞书文档导入。
---

# Feishu → NEC MDX

## 作用

把单篇飞书文档或整个飞书 Wiki 子树转换为符合 NEC 文档站规范的 `.mdx` 页面：

- 每个页面都有标准 YAML frontmatter（`title`、`description`）
- 图片下载到 `images/<topic>/`，引用路径统一为 `/images/<topic>/...`
- 媒体标签（`<image>`、`<file>`、`<whiteboard>`）转成 Markdown 语法或占位提示
- 自动在 `docs.json` 指定分组注册页面
- 运行 `tools/ci/check_docs.py` 确保无死链、frontmatter 合规

## 前置依赖

- 已安装并登录 `lark-cli`（参考 `~/.claude/skills/lark-shared/SKILL.md`）
- Python 3.10+
- 在项目根目录 `D:\Project_env\docs` 下执行

## 使用流程

### 1. 确认来源与目标

询问或推断：

| 问题 | 默认值 |
| --- | --- |
| 来源是单篇文档还是 Wiki 子树？ | `/docx/`、`/doc/` 为单篇；`/wiki/` 为子树 |
| 内容主题（用于图片目录与分组） | 从文档标题或用户指定 |
| 目标目录 | 项目内对应主题目录，如 `wiki/`、`mechanical/`、`competition/` |
| 注册到 `docs.json` 哪个 tab/group | 用户指定，不指定则不自动注册 |

### 2. 拉取飞书内容

```bash
python .kimi/skills/feishu-to-nec-mdx/scripts/fetch_feishu_content.py \
  --source "https://newenergycoder.feishu.cn/wiki/xxxxx" \
  --scope wiki \
  --out ./.feishu-mdx-export
```

输出：

- `.feishu-mdx-export/content.json`：标准化文档内容
- `.feishu-mdx-export/media-manifest.json`：图片/文件清单
- `.feishu-mdx-export/fetch-report.json`：拉取统计与跳过节点

### 3. 下载媒体到文档站目录

```bash
python .kimi/skills/feishu-to-nec-mdx/scripts/download_media.py \
  --manifest ./.feishu-mdx-export/media-manifest.json \
  --topic <topic> \
  --out ./images/<topic>
```

下载后 `media-manifest.json` 会更新 `local_path` 字段，供下一步生成 `.mdx` 时引用。

### 4. 生成 `.mdx`

```bash
python .kimi/skills/feishu-to-nec-mdx/scripts/build_mdx.py \
  --content ./.feishu-mdx-export/content.json \
  --topic <topic> \
  --out-dir ./<target-dir> \
  --base-url "/images/<topic>"
```

规则：

- 文件名使用文档标题的 slug，如 `my-title.mdx`
- 自动补全 `title` 与 `description` frontmatter
- 将飞书媒体标签替换为本地图片/文件链接
- 清理 `<view>` 等飞书私有标签
- 保留 Markdown 表格、代码块、列表、引用

### 5. 注册导航（可选但推荐）

```bash
python .kimi/skills/feishu-to-nec-mdx/scripts/register_nav.py \
  --docs-json ./docs.json \
  --tab "Wiki" \
  --group "Wiki 资源" \
  --pages wiki/new-page-1 wiki/new-page-2
```

如果目标 tab/group 不存在，先询问是否新建。

### 6. 运行 CI 检查

```bash
python tools/ci/check_docs.py
```

修复 frontmatter、死链、未注册页面等问题。

### 7. 提交

使用 Conventional Commits：

```bash
git add docs.json <target-dir>/ <images>/<topic>/
git commit -m "docs(<topic>): import from Feishu <source-title>"
```

## 质量标准

- 每个 `.mdx` 都有非空 `title` 和 `description`
- 无 `<image token="...">`、`<file token="...">`、`<whiteboard token="...">` 残留
- 图片引用路径以 `/images/<topic>/` 开头
- 内部链接为可解析的相对路径或站点根路径
- `docs.json` 中所有新增页面均已注册
- `tools/ci/check_docs.py` 通过

## 文件说明

| 脚本 | 作用 |
| --- | --- |
| `scripts/fetch_feishu_content.py` | 拉取飞书文档/Wiki 内容，输出标准化 JSON |
| `scripts/download_media.py` | 下载图片/文件到 `images/<topic>/` |
| `scripts/build_mdx.py` | 将 JSON 转换为 `.mdx` |
| `scripts/register_nav.py` | 在 `docs.json` 指定 tab/group 下注册页面 |

## 注意事项

- 不要公开私有飞书知识库的内容，导出前确认用户授权
- `sheet`、`bitable`、`slides`、`mindnote` 等类型不会被转换为 `.mdx`，会进入 `fetch-report.json` 的 `skipped_nodes`
- 飞书画板（whiteboard）默认导出为图片，如果下载失败则保留占位提示
