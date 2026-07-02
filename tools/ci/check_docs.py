#!/usr/bin/env python3
"""NEC 文档站健康检查脚本。

验证项目：
1. docs.json 是合法 JSON 且包含推荐字段
2. 导航中注册的页面存在对应 .mdx 或 .md 文件
3. 注册在导航中的 .mdx 文件包含 YAML frontmatter
4. frontmatter 包含 title 与 description
5. Markdown / MDX 中的内部链接可解析
6. 内部链接不包含非 ASCII 字符
7. 未重新引入已删除的归档目录（legacy/、api-reference/、essentials/）
8. 不存在指向 localhost 的内部链接
9. robots.txt 存在
10. 外部链接抽样健康检查（警告级别）
"""

from __future__ import annotations

import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

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
    "robots.txt",
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

# docs.json 推荐字段
RECOMMENDED_TOP_LEVEL = {"metadata", "search", "seo"}

# 已知可能不稳定、需要登录、或会拦截自动化请求的外部域名，仅提示不阻塞
EXTERNAL_LINK_ALLOWLIST = {
    "scn0bdoc8zxg.feishu.cn",
    "applink.feishu.cn",
    "www.feishu.cn",
    "lain-database.feishu.cn",
    "ncn61b7rswxm.feishu.cn",
    "wcn9j5638vrr.feishu.cn",
    "www.smartcarrace.com",
    "docs.qq.com",
    "pan.baidu.com",
    "gitee.com",
    "qm.qq.com",
    "www.cnrobocon.net",
    "docs.m2stud.io",
    "edu.csdn.net",
    "fishros.com",
    "lightburnsoftware.com",
    "openeuler.org",
    "www.rt-thread.io",
    "www.yahboom.com",
    "cdn.newenergycoder.club",
}


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


def parse_frontmatter(path: Path) -> dict[str, str] | None:
    """解析 YAML frontmatter，返回键值字典；无 frontmatter 返回 None。"""
    text = path.read_text(encoding="utf-8")
    if not text.lstrip().startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    fm_text = parts[1]
    result: dict[str, str] = {}
    for line in fm_text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def check_frontmatter_fields(path: Path) -> list[str]:
    """检查 frontmatter 是否包含非空 title 与 description。"""
    issues: list[str] = []
    rel = path.relative_to(ROOT).as_posix()
    fm = parse_frontmatter(path)
    if fm is None:
        return [f"缺少 YAML frontmatter: {rel}"]
    for field in ("title", "description"):
        value = fm.get(field, "")
        if not value or value.lower() in {"todo", "tbd", "待补充"}:
            issues.append(f"{rel}: frontmatter {field} 为空或待补充")
    return issues


def check_forbidden_paths() -> list[str]:
    errors: list[str] = []
    for name in FORBIDDEN_PATHS:
        p = ROOT / name
        if p.exists():
            errors.append(f"禁止的归档目录/文件仍然存在: {name}")
    return errors


def check_docs_json_fields(data: dict) -> list[str]:
    warnings: list[str] = []
    missing = RECOMMENDED_TOP_LEVEL - set(data.keys())
    if missing:
        warnings.append(f"docs.json 缺少推荐字段: {', '.join(sorted(missing))}")
    return warnings


def check_robots_txt() -> list[str]:
    warnings: list[str] = []
    robots = ROOT / "robots.txt"
    if not robots.is_file():
        warnings.append("缺少 robots.txt，搜索引擎与 AI 爬虫无法发现 sitemap/llms.txt")
    return warnings


# Markdown/MDX 中链接的正则
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
HTML_HREF_RE = re.compile(r"\b(?:href|src)=[\"']([^\"']+)[\"']", re.IGNORECASE)
CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```|~~~[\s\S]*?~~~")


def extract_links(text: str) -> set[str]:
    # 移除代码块中的内容，避免把示例链接当作真实引用检查
    text_without_code = CODE_BLOCK_RE.sub("", text)
    links: set[str] = set()
    for _, url in MD_LINK_RE.findall(text_without_code):
        links.add(url)
    for url in HTML_HREF_RE.findall(text_without_code):
        links.add(url)
    return links


def is_internal(url: str) -> bool:
    if not url:
        return False
    if url.startswith("mailto:") or url.startswith("tel:"):
        return False
    if url.startswith("http://") or url.startswith("https://") or url.startswith("//"):
        return False
    return True


def is_external(url: str) -> bool:
    return bool(url) and (
        url.startswith("http://") or url.startswith("https://") or url.startswith("//")
    )


def add_internal_link(links: set[str], url: str) -> None:
    url = url.split("#", 1)[0]
    url = url.split("?", 1)[0]
    if is_internal(url):
        if url.startswith("/"):
            links.add(url.lstrip("/"))


def extract_internal_links(text: str) -> set[str]:
    links: set[str] = set()
    for url in extract_links(text):
        add_internal_link(links, url)
    return links


def extract_external_links(text: str) -> set[str]:
    links: set[str] = set()
    for url in extract_links(text):
        if is_external(url):
            links.add(url)
    return links


def target_exists(url: str) -> bool:
    p = ROOT / url
    if p.exists() and p.is_file():
        return True
    for ext in PAGE_EXTS:
        if (p.with_suffix(ext)).is_file():
            return True
    return False


def check_external_url(url: str) -> str | None:
    """返回 None 表示检查通过，否则返回错误信息。"""
    parsed = urlparse(url)
    domain = parsed.netloc
    if domain in EXTERNAL_LINK_ALLOWLIST:
        return None  # 允许列表中的域名不阻塞

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (NEC-docs-ci/1.0)"}

    def try_method(method: str) -> tuple[int, str | None]:
        req = Request(url, method=method, headers=headers)
        try:
            with urlopen(req, timeout=8) as resp:
                return resp.status, None
        except HTTPError as exc:
            return exc.code, None
        except URLError as exc:
            return 0, f"URL 错误: {exc.reason}"
        except Exception as exc:
            return 0, f"请求异常: {exc}"

    # 先尝试 HEAD
    status, err = try_method("HEAD")
    if status and status < 400:
        return None
    # HEAD 失败时尝试 GET（部分站点不支持 HEAD 或针对 HEAD 返回 404）
    status, err = try_method("GET")
    if status and status < 400:
        return None
    if status:
        return f"HTTP {status}"
    return err


def main() -> int:
    data = load_docs_json()
    nav_pages = collect_nav_pages(data)

    errors: list[str] = []
    warnings: list[str] = []

    errors.extend(check_forbidden_paths())
    warnings.extend(check_docs_json_fields(data))
    warnings.extend(check_robots_txt())

    # 1. 导航页面存在性
    for page in sorted(nav_pages):
        if not page_exists(page):
            errors.append(f"导航页面缺少文件: {page}")

    # 2. 收集所有 .mdx 文件
    all_mdx = list(ROOT.rglob("*.mdx"))

    # 3. frontmatter 字段检查
    for path in all_mdx:
        issues = check_frontmatter_fields(path)
        for issue in issues:
            if "缺少 YAML frontmatter" in issue:
                errors.append(issue)
            else:
                errors.append(issue)

    # 4. 孤立页面检查
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

    # 5. 内部链接检查 + 外部链接收集
    all_external: set[str] = set()
    for path in all_mdx:
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        for link in extract_internal_links(text):
            if any(link.lower().endswith(ext) for ext in ASSET_EXTS) or link.lower().endswith(".svg"):
                if not target_exists(link):
                    errors.append(f"{rel}: 缺失图片/资源 {link}")
            else:
                if not target_exists(link):
                    errors.append(f"{rel}: 死链 {link}")
            if link.startswith("localhost") or "localhost:" in link:
                errors.append(f"{rel}: 包含 localhost 链接 {link}")
            try:
                link.encode("ascii")
            except UnicodeEncodeError:
                warnings.append(f"{rel}: 内部链接包含非 ASCII 字符，建议 Percent-Encoding: {link}")
        all_external.update(extract_external_links(text))

    # 6. 外部链接抽样检查（警告级别）
    external_list = sorted(all_external)
    if external_list:
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_url = {executor.submit(check_external_url, url): url for url in external_list}
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    if result:
                        warnings.append(f"外部链接可能失效: {url} ({result})")
                except Exception as exc:
                    warnings.append(f"外部链接检查异常: {url} ({exc})")

    # 7. style.css 存在性
    if not (ROOT / "style.css").is_file():
        warnings.append("style.css 不存在，请确认主题是否生效")

    # 输出报告
    print("=" * 60)
    print("NEC 文档站健康检查报告")
    print("=" * 60)
    print(f"导航页面数: {len(nav_pages)}")
    print(f"扫描 .mdx 文件数: {len(all_mdx)}")
    print(f"外部链接数: {len(external_list)}")

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
