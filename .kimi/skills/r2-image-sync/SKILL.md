---
name: r2-image-sync
description: 将 NEC 文档站中的本地图片批量上传到 Cloudflare R2，并自动把 .mdx 文档中的 /images/ 引用替换为 CDN 链接。触发词：同步图片到 R2、R2 图床同步、批量上传图片、替换图片链接。
---

# R2 图片同步

把 `images/` 目录下的图片批量上传到 Cloudflare R2 `docs` 桶，并将 `.mdx` 文档中的 `/images/...` 引用替换为 `https://cdn.newenergycoder.club/images/...`。

## 前置条件

1. R2 `docs` 桶已创建，并绑定自定义域 `cdn.newenergycoder.club`
2. `docs` 桶已开启**公开访问**（否则 CDN 链接会 403）
3. `docs` 桶 CORS 策略允许你的部署域名（本地开发需允许 `http://localhost:5500`）
4. 已配置以下环境变量：

| 环境变量 | 说明 | 示例 |
| --- | --- | --- |
| `R2_ENDPOINT` | R2 S3 Endpoint | `https://<account-id>.r2.cloudflarestorage.com` |
| `R2_ACCESS_KEY_ID` | S3 Access Key ID | `e5b80825...` |
| `R2_SECRET_ACCESS_KEY` | S3 Secret Access Key | `1db559fb...` |
| `R2_BUCKET` | 桶名称 | `docs` |
| `R2_CDN_BASE_URL` | 自定义域，末尾不带斜杠 | `https://cdn.newenergycoder.club` |

## 使用方法

### 1. 仅上传图片

```bash
python .kimi/skills/r2-image-sync/r2_image_sync.py upload
```

会扫描 `images/` 下所有图片，上传到 R2 `docs` 桶，保持 `images/<topic>/...` 的目录结构。

### 2. 仅替换文档链接

```bash
python .kimi/skills/r2-image-sync/r2_image_sync.py replace
```

会扫描项目中所有 `.mdx` 文件（除 `development.mdx` 等规范示例外），把 `/images/...` 替换为 CDN 链接。

### 3. 上传 + 替换（推荐）

```bash
python .kimi/skills/r2-image-sync/r2_image_sync.py sync
```

### 4. 删除本地图片

确认 CDN 可访问后：

```bash
python .kimi/skills/r2-image-sync/r2_image_sync.py clean
```

⚠️ 删除前务必确认 `https://cdn.newenergycoder.club/images/...` 能正常访问。

## 工作流程示例

```bash
# 配置环境变量
export R2_ENDPOINT="https://033b31d195ca339dcd4709b1a54b1bbf.r2.cloudflarestorage.com"
export R2_ACCESS_KEY_ID="e5b80825dfa4596a4f22f828a87cf05c"
export R2_SECRET_ACCESS_KEY="1db559fb193864fbf667761a155a394b03425762ef89476faff51b9c35002ca5"
export R2_BUCKET="docs"
export R2_CDN_BASE_URL="https://cdn.newenergycoder.club"

# 上传并替换
python .kimi/skills/r2-image-sync/r2_image_sync.py sync

# 检查 CI
python tools/ci/check_docs.py

# 确认 CDN 可访问后，清理本地图片
python .kimi/skills/r2-image-sync/r2_image_sync.py clean
```

## 注意事项

- 默认会跳过 `development.mdx`（含 `/images/` 引用规范示例）
- 不会重复替换已经是 CDN 链接的地址
- 上传前会检查 R2 上是否已存在同名对象，避免重复上传
- 替换完成后建议运行 `python tools/ci/check_docs.py` 验证
