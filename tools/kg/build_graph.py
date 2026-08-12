"""扫描 docs 仓库内所有已注册页面，解析页面间互链，生成知识图谱数据。

数据源：docs.json 的 navigation（只收录已注册页面，避免孤儿页干扰）。
输出：kg/graph-data.js（window.NEC_GRAPH = {...}，force-graph 兼容的 nodes/links 格式）。
注：Mintlify 不提供 .json 静态文件，故包装为 JS 全局变量。

用法：
    python tools/kg/build_graph.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_JSON = REPO_ROOT / "docs.json"
OUTPUT = REPO_ROOT / "kg" / "graph-data.js"

# 需要扫描的页面后缀
PAGE_SUFFIXES = {".mdx", ".md"}

# 组路径前缀 → 图谱分组标签（用于着色）
GROUP_COLORS = [
    ("index", "首页"),
    ("start-here/", "快速开始"),
    ("development", "快速开始"),
    ("training/", "10 日集训"),
    ("mechanical/", "机构 SIG"),
    ("vision/", "视觉与嵌入式"),
    ("embedded-software/", "视觉与嵌入式"),
    ("ai-tools/", "AI 工具"),
    ("templates/", "模板与规范"),
    ("solutions/", "解决方案"),
    ("competition/", "竞赛"),
    ("curc26/", "CURC 2026"),
    ("curc27/", "CURC 2027"),
    ("community/", "社区"),
    ("contributing", "贡献指南"),
    ("wiki/", "Wiki"),
    ("skills/", "技能库"),
    ("GOVERNANCE", "治理"),
    ("CODE_OF_CONDUCT", "治理"),
    ("SUPPORT", "治理"),
    ("SECURITY", "治理"),
    ("ROADMAP", "关于"),
    ("resource-index", "关于"),
]

# Markdown 链接 [text](target)，排除外链与图片
MD_LINK_RE = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)[^)]*\)")
# MDX 组件中的 href="/xxx"
HREF_RE = re.compile(r'href=["\'](/[^"\']*)["\']')
# frontmatter
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
TITLE_RE = re.compile(r'^title:\s*["\']?(.*?)["\']?\s*$', re.MULTILINE)
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
# 代码块（其中的"链接"不算互链）
CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)


def collect_pages(node, out: list[str]) -> None:
    """递归收集 docs.json navigation 中所有页面 ID。"""
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, dict):
        if "pages" in node:
            for p in node["pages"]:
                collect_pages(p, out)
        elif "tabs" in node:
            for t in node["tabs"]:
                collect_pages(t, out)
        elif "groups" in node:
            for g in node["groups"]:
                collect_pages(g, out)
    elif isinstance(node, list):
        for item in node:
            collect_pages(item, out)


def group_of(page_id: str) -> str:
    for prefix, label in GROUP_COLORS:
        if page_id == prefix.rstrip("/") or page_id.startswith(prefix):
            return label
    return "其他"


def read_title(path: Path, fallback: str) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return fallback
    m = FRONTMATTER_RE.match(text)
    if m:
        t = TITLE_RE.search(m.group(1))
        if t:
            return t.group(1)
    h1 = H1_RE.search(text)
    return h1.group(1) if h1 else fallback


def extract_links(text: str) -> list[str]:
    """提取正文中的站内链接目标（去掉代码块后匹配）。"""
    body = CODE_FENCE_RE.sub("", text)
    targets = [m.group(1) for m in MD_LINK_RE.finditer(body)]
    targets += HREF_RE.findall(body)
    return targets


def resolve_target(target: str, source_id: str) -> str | None:
    """把链接目标解析成页面 ID；解析不到（外链/锚点/静态资源）返回 None。"""
    if target.startswith(("http://", "https://", "mailto:", "#")):
        return None
    target = target.split("#", 1)[0].split("?", 1)[0]
    if not target:
        return None
    if target.startswith("/"):
        # 站内绝对路径：静态资源开头的一律排除
        if target.startswith(("/images/", "/logo/", "/favicon", "/public/", "/kg/")):
            return None
        candidate = target.lstrip("/")
    else:
        # 相对路径：相对源页面所在目录解析
        base = PurePosixPath(source_id).parent
        candidate = str(base.joinpath(target))
    # 归一化 ../
    parts: list[str] = []
    for part in PurePosixPath(candidate).parts:
        if part == "..":
            if parts:
                parts.pop()
        elif part not in (".", ""):
            parts.append(part)
    candidate = "/".join(parts)
    # 去掉后缀与 /index 归一
    stem = re.sub(r"\.(mdx|md)$", "", candidate)
    return stem


def main() -> int:
    config = json.loads(DOCS_JSON.read_text(encoding="utf-8"))
    page_ids: list[str] = []
    collect_pages(config.get("navigation", {}), page_ids)

    # 去重保序，且文件必须存在
    seen: set[str] = set()
    pages: dict[str, Path] = {}
    for pid in page_ids:
        if pid in seen:
            continue
        seen.add(pid)
        for suffix in PAGE_SUFFIXES:
            p = REPO_ROOT / f"{pid}{suffix}"
            if p.is_file():
                pages[pid] = p
                break
        else:
            print(f"[warn] 导航页找不到文件: {pid}", file=sys.stderr)

    # index 归一化别名：foo/index 与 foo 视为同一节点
    def canonical(pid: str) -> str:
        return pid[: -len("/index")] if pid.endswith("/index") else pid

    nodes: dict[str, dict] = {}
    for pid, path in pages.items():
        cid = canonical(pid)
        if cid in nodes:
            continue
        nodes[cid] = {
            "id": cid,
            "title": read_title(path, cid.rsplit("/", 1)[-1]),
            "group": group_of(pid),
            "url": f"/{cid}",
        }

    links: set[tuple[str, str]] = set()
    for pid, path in pages.items():
        src = canonical(pid)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for raw in extract_links(text):
            dst = resolve_target(raw, pid)
            if dst is None:
                continue
            dst = canonical(dst)
            if dst in nodes and dst != src:
                links.add((src, dst))

    # 统计度，用于节点大小
    degree: dict[str, int] = {cid: 0 for cid in nodes}
    for s, d in links:
        degree[s] += 1
        degree[d] += 1
    for cid, n in nodes.items():
        n["val"] = 1 + degree[cid]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "nodes": sorted(nodes.values(), key=lambda n: n["id"]),
        "links": [{"source": s, "target": d} for s, d in sorted(links)],
    }
    body = json.dumps(payload, ensure_ascii=False)
    OUTPUT.write_text(f"window.NEC_GRAPH = {body};\n", encoding="utf-8")
    print(f"nodes={len(nodes)} links={len(links)} -> {OUTPUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
