# 排障记录（feishu-doc-clone）

按出现顺序记录实操中踩过的坑，含报错原文与修法。

## 1. `+media-download` 对素材 403

```
"error": { "type": "network", "subtype": "transport", "code": 403, "message": "HTTP 403" }
```

`lark-cli` 自带的 `references/lark-doc-media-download.md` 排障节明确说：素材 403 时改用 `docs +media-preview`。
`+media-preview` 对图片能返回二进制（`saved_path` + `size_bytes`），流程上等效。

## 2. `--output` 必须是相对路径

```
"subtype": "invalid_argument", "message": "unsafe output path: resolve save path: --output must be a relative path"
```

`--output` 不接受绝对路径。修法：`subprocess.run(..., cwd=media_dir)`，`--output` 只传文件名。

## 3. Windows 下 `.cmd` 无法被 subprocess 直接 spawn

```
FileNotFoundError: [WinError 2] 系统找不到指定的文件
```

`lark-cli.cmd` 不是可执行文件，Python `subprocess.run(["lark-cli.cmd", ...])` 起不来。修法：
- 优先用真正的 `lark-cli.exe`（列表传参即可）；
- 非用 `.cmd` 不可时，拼成字符串 + `shell=True`。

## 4. lark-cli 自更新挪走 shim

会话中途 `npm/lark-cli.cmd` 突然 `No such file or directory`——npm 自更新把可执行文件挪进了
`npm/node_modules/@larksuite/.cli-<hash>/bin/lark-cli.exe`。
修法：`find_lark()` 按以下顺序探测：
1. `~/AppData/Roaming/npm/node_modules/@larksuite/.cli-*/bin/lark-cli.exe`
2. `~/AppData/Roaming/npm/lark-cli.cmd`
3. `~/AppData/Roaming/npm/lark-cli`
4. PATH 里的 `lark-cli`

## 5. 单次写入过大触发服务端超时

```
"subtype": "timeout", "message": "API call failed: server time out error"   # rc=4
```

实测：`+update --content` 超过约 2000~3000 字符就超时（成功的块是 25 / 2097 字符，失败的都是几千到上万）。
修法：按块级标签边界切成 `CHUNK_MAX=1500` 的小块逐块 append，绝不切断标签。

## 6. 部分下载文件无扩展名

部分响应没有 `Content-Type`，`--output asset` 落成无后缀文件 `asset`。
修法：按文件头魔数识别：

| 魔数 | 扩展名 |
|---|---|
| `\x89PNG` | `.png` |
| `\xff\xd8\xff` | `.jpg` |
| `GIF8` | `.gif` |
| 第 9~12 字节 `WEBP` | `.webp` |
| 含 `<svg` | `.svg` |

## 7. 写入中断留下孤儿块

`write_sections.py` 那版按 h1 切块（块太大），中断后 overwrite 又 append，导致文档**开头多一段重复内容**
（且那段里的图还是飞书内网 token 而非 CDN）。
修法：`write` 阶段用小块 + `state.json.written` 记录已完成分块，重跑先 overwrite 再续 append。
即便如此，仍建议跑完后人工核对开头/结尾无重复段落。

## 8. `sorted()` 混排 str 和 int

```
TypeError: '<' not supported between instances of 'str' and 'int'
```

`state.written` 里同时有 `"init"` 和分块序号 `0,1,2...`，直接 `sorted()` 报错。
修法：`sorted(done, key=str)`。
