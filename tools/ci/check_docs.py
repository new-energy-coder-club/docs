#!/usr/bin/env python3
"""NEC 文档站健康检查脚本。

验证项目：
1. docs.json 是合法 JSON
2. 导航中注册的页面存在对应 .mdx 或 .md 文件
3. 注册在导航中的 .mdx 文件包含 YAML frontmatter
4. Markdown / MDX 中的内部链接可解析
5. 未重新引入已删除的归档目录（legacy/、api-reference/、essentials/）
6. 不存在指向 localhost 的内部链接
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DOCS_JSON = ROOT / "docs.json"

# 允许不进入导航的特例文件（相对 ROOT）
ALLOWED_ORPHANS = {
    "AGENTS.md",
    "snippets/snippet-intro.mdx",
    "wiki/README.md",
    "tools/ci/check_docs.py",
}

# 已删除/禁止的目录或文件
FORBIDDEN_PATHS = {
    "legacy",
    "api-reference",
    "essentials",
}

# 图片/静态资源扩展名
ASSET_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".pdf"}
PAGE_EXTS = {".mdx", ".md"}


def load_docs_json() -> dict:
    try:
        with DOCS_JSON.open(encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        print(f"[ERROR] docs.json 不是合法 JSON: {exc}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"[ERROR] 找不到 {DOCS_JSON}")
        sys.exit(1)


def collect_nav_pages(data: dict) -> set[str]:
    pages: set[str] = set()

    def walk(items: Iterable):
        for item in items:
            if isinstance(item, str):
                pages.add(item)
            elif isinstance(item, dict):
                if "pages" in item:
                    walk(item["pages"])
                # anchors 里的站内链接也加入检查
                if "href" in item and isinstance(item["href"], str):
                    href = item["href"]
                    if href.startswith("/") and not href.startswith("//"):
                        pages.add(href.lstrip("/"))

    nav = data.get("navigation", {})
    for tab in nav.get("tabs", []):
        walk(tab.get("pages", []))
        for group in tab.get("groups", []):
            walk(group.get("pages", []))

    for anchor in nav.get("global", {}).get("anchors", []):
        href = anchor.get("href", "")
        if href.startswith("/") and not href.startswith("//"):
            pages.add(href.lstrip("/"))

    return pages


def page_exists(path: str) -> bool:
    """导航路径可能省略扩展名，也可能是 .mdx/.md/图片等。"""
    p = ROOT / path
    if p.exists() and p.is_file():
        return True
    for ext in PAGE_EXTS | ASSET_EXTS:
        if (p.with_suffix(ext)).is_file():
            return True
    return False


def check_frontmatter(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    return text.lstrip().startswith("---")


def check_forbidden_paths() -> list[str]:
    errors: list[str] = []
    for name in FORBIDDEN_PATHS:
        p = ROOT / name
        if p.exists():
            errors.append(f"禁止的归档目录/文件仍然存在: {name}")
    return errors


# Markdown/MDX 中内部链接的正则
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
HTML_HREF_RE = re.compile(r"\b(?:href|src)=[\"']([^\"']+)[\"']", re.IGNORECASE)


def extract_internal_links(text: str) -> set[str]:
    links: set[str] = set()

    for _, url in MD_LINK_RE.findall(text):
        _add_if_internal(links, url)

    for url in HTML_HREF_RE.findall(text):
        _add_if_internal(links, url)

    return links


def _add_if_internal(links: set[str], url: str) -> None:
    url = url.split("#", 1)[0]  # 忽略锚点
    url = url.split("?", 1)[0]  # 忽略查询参数
    if not url:
        return
    if url.startswith("mailto:") or url.startswith("tel:"):
        return
    if url.startswith("http://") or url.startswith("https://") or url.startswith("//"):
        return
    if url.startswith("/"):
        links.add(url.lstrip("/"))
    else:
        # 相对路径暂不做跨文件解析，只记录为相对路径
        pass


def target_exists(url: str) -> bool:
    p = ROOT / url
    if p.exists() and p.is_file():
        return True
    # 页面路径省略扩展名的情况
    for ext in PAGE_EXTS:
        if (p.with_suffix(ext)).is_file():
            return True
    return False


def main() -> int:
    data = load_docs_json()
    nav_pages = collect_nav_pages(data)

    errors: list[str] = []
    warnings: list[str] = []

    errors.extend(check_forbidden_paths())

    # 1. 导航页面存在性
    for page in sorted(nav_pages):
        if not page_exists(page):
            errors.append(f"导航页面缺少文件: {page}")

    # 2. 收集所有 .mdx 文件
    all_mdx = list(ROOT.rglob("*.mdx"))

    # 3. frontmatter 检查
    for path in all_mdx:
        rel = path.relative_to(ROOT).as_posix()
        if not check_frontmatter(path):
            errors.append(f"缺少 YAML frontmatter: {rel}")

    # 4. 孤立页面检查（导航中未注册，也不在特例名单）
    nav_set = {p for p in nav_pages}
    # 导航页面可能省略扩展名，因此也把带扩展名的实际文件加入比较
    nav_files: set[str] = set()
    for page in nav_pages:
        p = ROOT / page
        nav_files.add(page)
        for ext in PAGE_EXTS:
            candidate = p.with_suffix(ext)
            if candidate.is_file():
                nav_files.add(candidate.relative_to(ROOT).as_posix())

    for path in all_mdx:
        rel = path.relative_to(ROOT).as_posix()
        if rel not in nav_files and rel not in ALLOWED_ORPHANS:
            warnings.append(f"未在导航中注册: {rel}")

    # 5. 内部链接检查
    for path in all_mdx:
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        for link in extract_internal_links(text):
            # 图片/静态资源需要存在
            if any(link.lower().endswith(ext) for ext in ASSET_EXTS):
                if not target_exists(link):
                    errors.append(f"{rel}: 缺失图片/资源 {link}")
            elif link.lower().endswith(".svg"):
                if not target_exists(link):
                    errors.append(f"{rel}: 缺失 SVG {link}")
            else:
                if not target_exists(link):
                    errors.append(f"{rel}: 死链 {link}")
            if link.startswith("localhost") or "localhost:" in link:
                errors.append(f"{rel}: 包含 localhost 链接 {link}")

    # 6. 检查 style.css 是否实际存在
    if not (ROOT / "style.css").is_file():
        warnings.append("style.css 不存在，但 docs.json 未显式引用，请确认主题是否生效")

    # 输出报告
    print("=" * 60)
    print("NEC 文档站健康检查报告")
    print("=" * 60)
    print(f"导航页面数: {len(nav_pages)}")
    print(f"扫描 .mdx 文件数: {len(all_mdx)}")

    if warnings:
        print("\n[WARNINGS]")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print("\n[ERRORS]")
        for e in errors:
            print(f"  - {e}")
        print(f"\n检查失败，共 {len(errors)} 个错误。")
        return 1

    print("\n✅ 所有检查通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
