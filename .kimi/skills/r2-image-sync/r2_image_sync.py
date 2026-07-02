#!/usr/bin/env python3
"""R2 图片同步工具：上传本地图片到 Cloudflare R2，并替换 .mdx 中的图片链接。"""

from __future__ import annotations

import argparse
import mimetypes
import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

import boto3
from botocore.config import Config

ROOT = Path(__file__).resolve().parents[3]
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}
EXCLUDE_FILES = {
    "development.mdx",  # 包含 /images/ 引用规范示例
}


def get_config() -> dict[str, str]:
    required = ["R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET", "R2_CDN_BASE_URL"]
    cfg = {}
    missing = []
    for key in required:
        value = os.environ.get(key)
        if not value:
            missing.append(key)
        cfg[key] = value or ""
    if missing:
        print("[ERROR] 缺少环境变量:", ", ".join(missing))
        sys.exit(1)
    cfg["R2_CDN_BASE_URL"] = cfg["R2_CDN_BASE_URL"].rstrip("/")
    return cfg


def get_s3_client(cfg: dict[str, str]):
    return boto3.client(
        "s3",
        endpoint_url=cfg["R2_ENDPOINT"],
        aws_access_key_id=cfg["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=cfg["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


def collect_local_images() -> list[Path]:
    images_dir = ROOT / "images"
    if not images_dir.exists():
        return []
    return [
        p for p in images_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    ]


def upload_images(cfg: dict[str, str]) -> tuple[int, int]:
    s3 = get_s3_client(cfg)
    bucket = cfg["R2_BUCKET"]
    files = collect_local_images()
    if not files:
        print("[INFO] 没有找到需要上传的图片")
        return 0, 0

    # 收集已存在的对象
    existing: set[str] = set()
    resp = s3.list_objects_v2(Bucket=bucket, Prefix="images/")
    existing.update(obj["Key"] for obj in resp.get("Contents", []))
    while resp.get("IsTruncated"):
        resp = s3.list_objects_v2(Bucket=bucket, Prefix="images/", ContinuationToken=resp["NextContinuationToken"])
        existing.update(obj["Key"] for obj in resp.get("Contents", []))

    uploaded = 0
    skipped = 0
    for p in files:
        key = p.relative_to(ROOT).as_posix()
        if key in existing:
            print(f"[SKIP] {key}")
            skipped += 1
            continue
        content_type, _ = mimetypes.guess_type(str(p))
        if not content_type:
            content_type = "application/octet-stream"
        print(f"[UPLOAD] {key} ({p.stat().st_size / 1024 / 1024:.2f} MB)")
        s3.upload_file(str(p), bucket, key, ExtraArgs={"ContentType": content_type})
        uploaded += 1

    print(f"\n上传完成：新增 {uploaded} 个，跳过 {skipped} 个，总计 {len(files)} 个")
    return uploaded, skipped


def is_external_url(url: str) -> bool:
    return bool(url) and (url.startswith("http://") or url.startswith("https://") or url.startswith("//"))


def replace_url(url: str, cdn_base: str) -> str | None:
    if is_external_url(url):
        return None
    if url.startswith("/images/"):
        return cdn_base + url
    return None


def replace_in_file(path: Path, cdn_base: str) -> int:
    text = path.read_text(encoding="utf-8")
    original = text

    # Markdown 图片/链接: ![alt](url)
    def md_repl(match: re.Match) -> str:
        alt, url = match.groups()
        new_url = replace_url(url, cdn_base)
        if new_url is None:
            return match.group(0)
        return f"![{alt}]({new_url})"

    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", md_repl, text)

    # HTML src/href: src="url" 或 src='url'
    def html_repl(match: re.Match) -> str:
        attr, quote, url = match.groups()
        new_url = replace_url(url, cdn_base)
        if new_url is None:
            return match.group(0)
        return f"{attr}={quote}{new_url}{quote}"

    text = re.sub(r"\b(href|src)=([\"'])([^\"']+)\2", html_repl, text, flags=re.IGNORECASE)

    count = (original != text)
    if text != original:
        # 统计实际替换次数
        count = original.count("/images/") - text.count("](/images/") - text.count('src="/images/') - text.count("src='/images/")
        # 更简单的统计：统计 CDN 链接新增数量
        count = text.count(cdn_base + "/images/") - original.count(cdn_base + "/images/")
        path.write_text(text, encoding="utf-8")
    return max(0, count)


def replace_links(cfg: dict[str, str]) -> int:
    cdn_base = cfg["R2_CDN_BASE_URL"]
    total = 0
    for path in sorted(ROOT.rglob("*.mdx")):
        rel = path.relative_to(ROOT).as_posix()
        if path.name in EXCLUDE_FILES:
            continue
        count = replace_in_file(path, cdn_base)
        if count > 0:
            print(f"[REPLACED] {rel}: {count} occurrences")
            total += count
    print(f"\n链接替换完成：共 {total} 处")
    return total


def clean_local_images() -> int:
    images_dir = ROOT / "images"
    if not images_dir.exists():
        print("[INFO] images/ 目录不存在")
        return 0

    files = list(images_dir.rglob("*"))
    files = [p for p in files if p.is_file()]
    if not files:
        print("[INFO] 没有本地图片可删除")
        return 0

    for p in files:
        print(f"[DELETE] {p.relative_to(ROOT).as_posix()}")
        p.unlink()

    # 删除空目录
    for dir_path in sorted(images_dir.rglob("*"), reverse=True):
        if dir_path.is_dir() and not any(dir_path.iterdir()):
            dir_path.rmdir()

    if images_dir.exists() and not any(images_dir.iterdir()):
        images_dir.rmdir()
        print("[DELETE] images/")

    print(f"\n清理完成：删除 {len(files)} 个本地图片文件")
    return len(files)


def main() -> int:
    parser = argparse.ArgumentParser(description="R2 图片同步工具")
    parser.add_argument("command", choices=["upload", "replace", "sync", "clean"], help="操作命令")
    args = parser.parse_args()

    cfg = get_config()

    if args.command == "upload":
        upload_images(cfg)
    elif args.command == "replace":
        replace_links(cfg)
    elif args.command == "sync":
        upload_images(cfg)
        print()
        replace_links(cfg)
    elif args.command == "clean":
        clean_local_images()

    return 0


if __name__ == "__main__":
    sys.exit(main())
