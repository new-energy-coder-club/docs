---
name: feishu-doc-clone
description: 把一篇飞书文档（docx）完整克隆成新文档——正文原样搬运，全部图片下载后上传 Cloudflare R2，再用 CDN 链接重写。断点续跑、按块写入规避服务端超时。用于跨空间/跨账号备份飞书文档、把飞书内容沉淀到带 CDN 图床的可分享文档。触发词：克隆飞书文档、复制飞书文档带图、飞书文档图片上 R2、备份飞书文档、feishu clone doc。
---

# 飞书文档克隆（正文 + 图片上 R2）

把**单篇**飞书 docx 完整复制成一篇新文档：正文逐块搬运，所有图片下载 → 上传 R2 → 改写成 `https://cdn.newenergycoder.club/...` 公网链接，新文档不再依赖源文档的访问权限。

与 `feishu-to-nec-mdx` 的区别：那个 skill 是**拉取飞书内容转成 Mintlify `.mdx`**；本 skill 是**在飞书内部复制一篇文档**，图片托管到 R2。

## 前置依赖

- 已安装并 `lark-cli auth login`（脚本自动在 `~/AppData/Roaming/npm/node_modules/@larksuite/.cli-*/bin/lark-cli.exe` 等路径找可执行文件）
- Python 3.10+，且 `boto3` 可用
- R2 凭证：`~/.kimi/skills/r2-image-sync/r2_image_sync.py` 内置常量（脚本自动正则读取），或环境变量 `R2_ENDPOINT` / `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` / `R2_BUCKET` / `R2_CDN_BASE_URL`
- **你对源文档有可读权限**；新文档建在**当前用户的「我的空间」**

## 用法

```bash
python .kimi/skills/feishu-doc-clone/scripts/clone_feishu_doc.py \
  --source "https://xxx.feishu.cn/docx/<token>" \
  --r2-prefix "images/<topic>/" \
  --title "新文档标题"            # 可选，默认沿用源标题
```

跑完输出新文档 URL。**中断后重跑同一条命令即可**（状态存 `<workdir>/state.json`，自动跳过已完成的下载/上传/写入分块）。

## 流程

| 阶段 | 做什么 | 关键产物 |
|---|---|---|
| fetch | `docs +fetch --detail with-ids` 拉全文 | `source-full.json` |
| download | 逐个 `+media-preview` 下载 `<img src="token">` | `media/`、`state.json.img_map` |
| upload | 上传 R2、重写 img 为 CDN、剥 block id | `rewritten.xml`、`state.json.r2_url` |
| create | `+create --parent-position my_library` 建空文档 | `state.json.target_doc` |
| write | 按块边界切成 ~1500 字符小块逐块 append | `chunks/g*.xml`、`state.json.written` |

## 已知坑（都是这次实操踩出来的）

- **`+media-download` 对部分素材返回 HTTP 403** → 改用 `+media-preview`（能拿到图片二进制）。
- **单次 `+update --content` 超过约 2000~3000 字符会触发飞书 `server time out error`（rc=4）** → 必须按块级标签边界切成 ~1500 字符小块，逐块 append；`CHUNK_MAX=1500`。
- **lark-cli 自更新会把 shim 从 `npm/lark-cli.cmd` 挪走**（中途 PATH 失效）→ 脚本优先用 `node_modules/@larksuite/.cli-*/bin/lark-cli.exe`。
- **`.cmd` 在 Python `subprocess` 里直接 spawn 会 `WinError 2`** → `.cmd` 必须 `shell=True`；`.exe` 不用。
- **部分响应无 `Content-Type`**，下载落成无后缀文件 → 按魔数（PNG/JPG/GIF/WEBP/SVG）补扩展名。
- **R2 凭证严禁提交进 git**；`scripts/` 下脚本可提交，运行产生的 `<workdir>/`（含 media、state.json）不要提交。
- **overwrite 清空后再 append**：若上一次写入中断留下残缺块，重跑会先 overwrite 全量重写，**但飞书侧已渲染的孤儿块需人工核对**（本次实操出现过开头残留一段重复内容）。

## 质量自检

跑完后：

1. `lark-cli docs +fetch --doc <new_doc> --scope outline --max-depth 2` —— 章节数与源文档一致、无重复 h1
2. `rewritten.xml` 里 `src="(?!https://)"` 残留应为 0
3. 抽查一张 CDN 图 `curl -A "Mozilla/5.0" <url>` 返回 200

## 文件

| 文件 | 作用 |
|---|---|
| `scripts/clone_feishu_doc.py` | 一体化克隆脚本（download → upload → create → write，断点续跑） |
| `references/troubleshooting.md` | 详细排障记录（含报错原文与对应修法） |
