# NEC 社区文档站点

本目录包含 NEC (New Energy Coder) 新能源开发者社区的文档站点配置。站点同时支持 **Sphinx + Read the Docs** 和 **Mintlify** 两种构建/部署方式，内容源以 Sphinx 为主，通过 Git 同步到 Mintlify 发布。

在线地址：
- Mintlify 站点：https://docs.newenergycoder.club/
- Read the Docs：见 `.readthedocs.yaml` 配置

## 📁 目录结构

```
docs/
├── .readthedocs.yaml      # Read the Docs 构建配置
├── .gitignore             # 忽略 Sphinx _build/
├── conf.py                # Sphinx 配置文件
├── docs.json              # Mintlify 配置
├── index.rst              # Sphinx 文档首页
├── requirements.txt       # Python 依赖
├── 404.rst                # 404 错误页面
├── README.md              # 本文件
│
├── _static/               # 静态资源（CSS/JS/图片）
├── _templates/            # HTML 模板
│
├── wiki/                  # 飞书 Wiki 导出文档
│   ├── index.rst
│   ├── README.md
│   └── *.md
│
├── start-here/            # 新手上路
├── competitions/          # 竞赛文档索引
├── projects/              # 项目文档索引
├── community/             # 社区与贡献
├── learn/                 # 学习资源
├── contribute/            # 贡献指南
├── curc26/                # CURC26 赛季
├── nec-plus/              # NEC+ 付费会员
├── nec_quickstart/        # 快速开始
└── ...
```

## 🚀 本地构建（Sphinx）

### 安装依赖

```bash
cd docs
pip install -r requirements.txt
```

### 构建 HTML

```bash
# 方法 1: 使用 Sphinx 直接构建
sphinx-build -b html . _build/html

# 方法 2: 使用 Makefile (Linux/Mac)
make html

# 方法 3: 使用 make.bat (Windows)
make.bat html
```

### 预览

```bash
cd _build/html
python -m http.server 8000
# 访问 http://localhost:8000
```

## 🌐 部署

### Mintlify

项目已配置 Mintlify，GitHub 仓库变更会自动触发部署：

- 仓库：https://github.com/new-energy-coder-club/docs
- 在线站点：https://docs.newenergycoder.club/

### Read the Docs

文档仍保留 Read the Docs 构建配置：

- 配置文件：`docs/.readthedocs.yaml`
- Sphinx 配置：`docs/conf.py`
- 依赖文件：`docs/requirements.txt`
- 首页文档：`docs/index.rst`

## 📝 文档格式

本站支持两种文档格式：

1. **reStructuredText (.rst)** - Sphinx 原生格式
2. **Markdown (.md)** - 通过 MyST Parser 支持

### 添加新页面

在 `index.rst` 中的 `toctree` 添加新文件路径：

```rst
.. toctree::
   :maxdepth: 2
   :caption: 新分类

   new-file          # 对应 new-file.rst 或 new-file.md
   folder/index      # 子目录
```

### 跨文件链接

RST 格式：
```rst
:doc:`页面标题 <path/to/file>`
```

Markdown 格式：
```markdown
[页面标题](path/to/file.md)
```

## 🔁 飞书 Wiki 导入

仓库提供了 `tools/feishu-import/` 脚本，用于将 NEC 飞书 Wiki 内容导入为 Sphinx/Markdown 文档：

```bash
# 从父仓库进入工具目录
cd ../tools/feishu-import

# 导入顶层 Wiki 节点
python import_wiki_top_level.py \
  --source "https://scn0bdoc8zxg.feishu.cn/wiki/S10LwzVZdiWLwxkEnEqcTcmEn6e" \
  --nodes-json /path/to/nodes.json \
  --out-dir ../../docs/wiki
```

脚本说明：
- `fetch_feishu_content.py`：修复 Windows 兼容性的 feishu-doc-webify 抓取脚本
- `import_wiki_top_level.py`：将飞书 Wiki 顶层节点转换为 Markdown 并导入 `docs/wiki/`

## 🔧 配置说明

### conf.py 关键配置

| 配置项 | 说明 |
|--------|------|
| `project` | 项目名称 |
| `html_theme` | 主题 (sphinx_rtd_theme) |
| `extensions` | 启用的扩展 |
| `myst_enable_extensions` | MyST Markdown 扩展 |

### 启用的扩展

- `myst_parser` - Markdown 支持
- `sphinx_copybutton` - 代码复制按钮
- `sphinx_tabs.tabs` - 选项卡支持
- `sphinxcontrib.mermaid` - Mermaid 图表
- `sphinxext.opengraph` - OpenGraph 元数据
- `notfound.extension` - 404 页面

## 📚 参考资源

- [Sphinx 文档](https://www.sphinx-doc.org/)
- [MyST Parser 文档](https://myst-parser.readthedocs.io/)
- [Read the Docs 文档](https://docs.readthedocs.io/)
- [RTD Theme 文档](https://sphinx-rtd-theme.readthedocs.io/)
- [Mintlify 文档](https://www.mintlify.com/docs)

## 🤝 贡献

如需更新文档，请：

1. 修改相关 `.rst` 或 `.md` 文件
2. 本地构建验证 `sphinx-build -b html . _build/html`
3. 提交 PR 到主分支

详细的贡献指南请参考：[CONTRIBUTING.md](../CONTRIBUTING.md)
