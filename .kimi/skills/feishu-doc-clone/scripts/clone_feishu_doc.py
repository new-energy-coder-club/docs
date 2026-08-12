#!/usr/bin/env python3
"""把一篇飞书文档（docx）完整克隆到当前用户的「我的空间」，图片上传到 Cloudflare R2。

用法：
    python clone_feishu_doc.py --source <docx_token或URL> [--title 新标题] \
        [--r2-prefix images/<topic>/] [--workdir <临时目录>]

流程（四阶段，均可断点续跑）：
    download  用 lark-cli +media-preview 把全部 <img src="token"> 下载到 <workdir>/media/
    upload    上传 media/ 到 R2，重写 XML 的 img 为 CDN URL，输出 <workdir>/rewritten.xml
    create    在「我的空间」创建空目标文档，记录 document_id 到 <workdir>/state.json
    write     把 rewritten.xml 按块级标签边界聚合成 ~1500 字符小块，逐块 append

幂等：状态存 <workdir>/state.json，重跑自动跳过已完成阶段/分块。

依赖：
    - lark-cli（已 auth login）；脚本自动在常见路径找 lark-cli.exe
    - R2 凭证：从 ~/.kimi/skills/r2-image-sync/r2_image_sync.py 正则读取（内置常量），
      或回退环境变量 R2_ENDPOINT / R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY / R2_BUCKET / R2_CDN_BASE_URL
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import subprocess
import sys
import time
from pathlib import Path

CHUNK_MAX = 1500  # 单次 append 超过约 2000~3000 字符会触发飞书服务端超时

# ---------------- 定位 lark-cli ----------------
def find_lark() -> str:
    candidates = []
    npm = Path.home() / "AppData/Roaming/npm"
    # 自更新后 shim 可能被挪进 node_modules/@larksuite/.cli-*/bin/lark-cli.exe
    candidates += sorted((npm / "node_modules/@larksuite").glob(".cli-*/bin/lark-cli.exe"))
    candidates += [npm / "lark-cli.cmd", npm / "lark-cli"]
    for c in candidates:
        if c.exists():
            return str(c)
    # 兜底：交给 PATH
    return "lark-cli"

LARK = find_lark()

def run_lark(args, cwd=None, tries=5):
    """调用 lark-cli，网络超时（rc=4 / subtype=timeout）指数退避重试。
    Windows 下 .cmd 必须用 shell=True；.exe 用列表即可。"""
    is_cmd = LARK.lower().endswith(".cmd")
    for t in range(tries):
        if is_cmd:
            cmd = " ".join([f'"{LARK}"'] + args)
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", cwd=cwd)
        else:
            r = subprocess.run([LARK] + args, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", cwd=cwd)
        blob = (r.stderr or "") + (r.stdout or "")
        if r.returncode == 0:
            return True, r.stdout
        if '"subtype": "timeout"' in blob or r.returncode == 4:
            time.sleep(2 * (2 ** t))
            continue
        return False, blob[:400]
    return False, "重试多次仍超时"

# ---------------- R2 配置 ----------------
def load_r2_config():
    cfg = {}
    sync = Path.home() / ".kimi/skills/r2-image-sync/r2_image_sync.py"
    if sync.exists():
        src = sync.read_text(encoding="utf-8")
        for k in ["R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET", "R2_CDN_BASE_URL"]:
            m = re.search(rf'{k}\s*=\s*"([^"]+)"', src)
            if m:
                cfg[k] = m.group(1)
    for k in ["R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET", "R2_CDN_BASE_URL"]:
        cfg.setdefault(k, os.environ.get(k, ""))
    missing = [k for k, v in cfg.items() if not v]
    if missing:
        sys.exit(f"缺少 R2 配置: {missing}（检查 r2_image_sync.py 或环境变量）")
    return cfg

# ---------------- 状态 ----------------
class State:
    def __init__(self, path: Path):
        self.path = path
        self.data = json.load(open(path, encoding="utf-8")) if path.exists() else {}

    def save(self):
        json.dump(self.data, open(self.path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)

# ---------------- 工具 ----------------
def detect_ext(p: Path) -> str:
    head = p.read_bytes()[:200]
    if head.startswith(b"\x89PNG"): return ".png"
    if head.startswith(b"\xff\xd8\xff"): return ".jpg"
    if head.startswith(b"GIF8"): return ".gif"
    if head[8:12] == b"WEBP": return ".webp"
    if b"<svg" in head.lower(): return ".svg"
    return ".png"

def fetch_source(source: str, workdir: Path) -> str:
    out = workdir / "source-full.json"
    if out.exists():
        return json.load(open(out, encoding="utf-8"))["data"]["document"]["content"]
    ok, stdout = run_lark(["docs", "+fetch", "--doc", source, "--detail", "with-ids"])
    if not ok:
        sys.exit(f"拉取源文档失败: {stdout}")
    out.write_text(stdout, encoding="utf-8")
    return json.loads(stdout)["data"]["document"]["content"]

# ---------------- 阶段 1：下载图片 ----------------
def stage_download(content: str, workdir: Path, state: State):
    media = workdir / "media"
    media.mkdir(exist_ok=True)
    tokens = list(dict.fromkeys(re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', content)))
    print(f"[download] {len(tokens)} 个唯一图片 token", flush=True)
    img_map = state.data.setdefault("img_map", {})
    for i, tok in enumerate(tokens, 1):
        if tok in img_map:
            continue
        out_name = f"{i:03d}-{tok}"
        ok, msg = run_lark(["docs", "+media-preview", "--token", tok, "--output", out_name],
                           cwd=str(media))
        matches = list(media.glob(f"{out_name}.*"))
        no_ext = media / out_name
        if not matches and no_ext.exists():
            renamed = no_ext.with_suffix(detect_ext(no_ext))
            no_ext.rename(renamed)
            matches = [renamed]
        if not matches:
            print(f"[download {i}/{len(tokens)}] FAIL {tok}: {msg[:150]}", flush=True)
            continue
        img_map[tok] = matches[0].name
        state.save()
        print(f"[download {i}/{len(tokens)}] {matches[0].name}", flush=True)
    print(f"[download] 完成 {len(img_map)}/{len(tokens)}", flush=True)

# ---------------- 阶段 2：上传 R2 + 重写 XML ----------------
def stage_upload(content: str, workdir: Path, state: State, r2_prefix: str):
    import boto3
    from botocore.config import Config
    cfg = load_r2_config()
    if not r2_prefix.endswith("/"):
        r2_prefix += "/"
    s3 = boto3.client("s3", endpoint_url=cfg["R2_ENDPOINT"],
                      aws_access_key_id=cfg["R2_ACCESS_KEY_ID"],
                      aws_secret_access_key=cfg["R2_SECRET_ACCESS_KEY"],
                      region_name="auto", config=Config(signature_version="s3v4"))
    existing = set()
    resp = s3.list_objects_v2(Bucket=cfg["R2_BUCKET"], Prefix=r2_prefix)
    existing.update(o["Key"] for o in resp.get("Contents", []))
    while resp.get("IsTruncated"):
        resp = s3.list_objects_v2(Bucket=cfg["R2_BUCKET"], Prefix=r2_prefix,
                                  ContinuationToken=resp["NextContinuationToken"])
        existing.update(o["Key"] for o in resp.get("Contents", []))

    img_map = state.data.get("img_map", {})
    r2_url = state.data.setdefault("r2_url", {})
    media = workdir / "media"
    for i, (tok, fname) in enumerate(img_map.items(), 1):
        if tok in r2_url:
            continue
        local = media / fname
        if not local.exists():
            print(f"[upload {i}] MISS {fname}", flush=True)
            continue
        key = r2_prefix + fname
        url = f"{cfg['R2_CDN_BASE_URL']}/{key}"
        if key not in existing:
            ctype, _ = mimetypes.guess_type(str(local))
            s3.upload_file(str(local), cfg["R2_BUCKET"], key,
                           ExtraArgs={"ContentType": ctype or "application/octet-stream"})
        r2_url[tok] = url
        state.save()
        print(f"[upload {i}/{len(img_map)}] {fname}", flush=True)

    # 重写 XML
    def img_repl(m):
        tag = m.group(0)
        src_m = re.search(r'\bsrc="([^"]+)"', tag)
        if not src_m:
            return tag
        url = r2_url.get(src_m.group(1))
        if not url:
            return "<p>📷 图片（未迁移成功）</p>"
        alt_m = re.search(r'\balt="([^"]*)"', tag)
        alt = (alt_m.group(1) if alt_m else "").replace('"', "'")
        return f'<img href="{url}" alt="{alt}"/>'

    content = re.sub(r"<img\b[^>]*?/>", img_repl, content)
    content = re.sub(r'\s+id="[^"]*"', "", content)   # 剥掉源 block id
    content = re.sub(r"<title>.*?</title>", "", content, count=1)  # 标题走 --title
    (workdir / "rewritten.xml").write_text(content, encoding="utf-8")
    ok = len(re.findall(r'<img href="https://', content))
    leftover = len(re.findall(r'src="(?!https://)[^"]+"', content))
    print(f"[upload] 重写完成 {len(content)} 字符，CDN img {ok}，非CDN src 残留 {leftover}", flush=True)

# ---------------- 阶段 3：创建目标文档 ----------------
def stage_create(state: State, title: str | None):
    if state.data.get("target_doc"):
        return state.data["target_doc"]
    title_xml = f"<title>{title}</title>" if title else "<title>迁移文档</title>"
    ok, stdout = run_lark(["docs", "+create", "--content",
                           title_xml + "<p>　</p>", "--parent-position", "my_library"])
    if not ok:
        sys.exit(f"创建目标文档失败: {stdout}")
    doc_id = json.loads(stdout)["data"]["document"]["document_id"]
    state.data["target_doc"] = doc_id
    state.save()
    print(f"[create] 目标文档 {doc_id}", flush=True)
    return doc_id

# ---------------- 阶段 4：分块写入 ----------------
def stage_write(workdir: Path, state: State):
    doc_id = state.data["target_doc"]
    content = (workdir / "rewritten.xml").read_text(encoding="utf-8")
    atoms = re.split(r'(?=<(?:h1|h2|h3|h4|p|callout|ul|ol|table|img|blockquote|grid|pre|figure|hr|checkbox)\b)', content)
    atoms = [a for a in atoms if a.strip()]
    groups, cur = [], ""
    for a in atoms:
        if cur and len(cur) + len(a) > CHUNK_MAX:
            groups.append(cur); cur = a
        else:
            cur += a
    if cur:
        groups.append(cur)
    print(f"[write] {len(groups)} 个写入块（原子块 {len(atoms)}）", flush=True)

    chunks = workdir / "chunks"
    chunks.mkdir(exist_ok=True)
    for i, g in enumerate(groups):
        (chunks / f"g{i:03d}.xml").write_text(g, encoding="utf-8")

    done = set(state.data.setdefault("written", []))

    def update(command, f: Path):
        rel = f.relative_to(workdir).as_posix()
        return run_lark(["docs", "+update", "--doc", doc_id, "--command", command,
                         "--content", f"@{rel}"], cwd=str(workdir))

    if "init" not in done:
        init_f = chunks / "_init.xml"
        init_f.write_text("<p>　</p>", encoding="utf-8")
        ok, msg = update("overwrite", init_f)
        if not ok:
            sys.exit(f"清空目标文档失败: {msg}")
        done.add("init"); state.save()
        print("[write] 已清空目标文档", flush=True)
        time.sleep(2)

    failed = []
    for i in range(len(groups)):
        if i in done:
            continue
        ok, msg = update("append", chunks / f"g{i:03d}.xml")
        if ok:
            done.add(i); state.save()
            print(f"[write {i+1}/{len(groups)}] OK", flush=True)
        else:
            print(f"[write {i+1}/{len(groups)}] FAIL: {msg}", flush=True)
            failed.append(i)
        time.sleep(1.0)
    state.data["written"] = sorted(done, key=str)
    state.save()
    print(f"[write] 完成 {len(done)-1}/{len(groups)}，失败 {len(failed)} -> {failed}", flush=True)
    return failed

# ---------------- main ----------------
def main():
    ap = argparse.ArgumentParser(description="克隆飞书文档到我的空间，图片上 R2")
    ap.add_argument("--source", required=True, help="源 docx token 或 URL")
    ap.add_argument("--title", default=None, help="新文档标题（默认沿用源标题）")
    ap.add_argument("--r2-prefix", default="images/feishu-clone/", help="R2 对象前缀")
    ap.add_argument("--workdir", default=None, help="临时目录（默认 ./.clone-<token8>）")
    args = ap.parse_args()

    m = re.search(r"(?:docx/|^)([A-Za-z0-9]{20,})", args.source)
    token = m.group(1) if m else args.source
    workdir = Path(args.workdir) if args.workdir else Path(f".clone-{token[:8]}")
    workdir.mkdir(exist_ok=True)
    state = State(workdir / "state.json")

    content = fetch_source(args.source, workdir)
    if args.title is None:
        t = re.search(r"<title[^>]*>(.*?)</title>", content)
        args.title = (t.group(1).strip() if t else "迁移文档")
        print(f"沿用源标题: {args.title}", flush=True)

    stage_download(content, workdir, state)
    stage_upload(content, workdir, state, args.r2_prefix)
    stage_create(state, args.title)
    failed = stage_write(workdir, state)

    doc_id = state.data["target_doc"]
    print(f"\n完成: https://www.feishu.cn/docx/{doc_id}", flush=True)
    sys.exit(0 if not failed else 1)

if __name__ == "__main__":
    main()
