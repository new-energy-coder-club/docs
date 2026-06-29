#!/usr/bin/env python3
"""Build NEC Mintlify .mdx files from feishu-doc-webify content.json."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


MEDIA_TAG_RE = re.compile(r"<(image|file|whiteboard)\b([^>]*)/?>", re.IGNORECASE)
VIEW_TAG_RE = re.compile(r"</?view\b[^>]*>", re.IGNORECASE)
ATTR_RE = re.compile(r'([A-Za-z_:-]+)="([^"]*)"')
FRONTMATTER_CHARS = re.compile(r"[^a-zA-Z0-9\u4e00-\u9fa5\s.,;:!?，。；：！？\"'()-]")


def parse_attrs(raw: str) -> dict[str, str]:
    return {match.group(1): match.group(2) for match in ATTR_RE.finditer(raw)}


def load_media_lookup(content: dict, content_path: Path) -> dict[str, dict]:
    """Build token -> media item map from content and sibling manifest."""
    lookup: dict[str, dict] = {}
    for item in content.get("media", []) or []:
        token = item.get("token")
        if token:
            lookup[token] = item
    sibling_manifest = content_path.parent / "media-manifest.json"
    if sibling_manifest.exists():
        manifest = json.loads(sibling_manifest.read_text(encoding="utf-8"))
        for item in manifest.get("media", []) or []:
            token = item.get("token")
            if token:
                lookup.setdefault(token, {}).update(item)
    return lookup


def local_url(local_path: str | None, base_url: str) -> str | None:
    if not local_path:
        return None
    path = Path(local_path)
    filename = path.name
    base = base_url.rstrip("/")
    return f"{base}/{filename}"


def media_replacer(media_lookup: dict[str, dict], base_url: str, topic: str) -> callable:
    def replace(match: re.Match) -> str:
        kind = match.group(1).lower()
        attrs = parse_attrs(match.group(2))
        token = attrs.get("token", "")
        token = re.sub(r"\s+", "", token) if token else ""
        name = attrs.get("name") or "media"
        item = media_lookup.get(token or "", {}) if token else {}
        url = local_url(item.get("local_path"), base_url)

        if url:
            if kind in {"image", "whiteboard"}:
                return f"![{name}]({url})"
            return f"[{name}]({url})"

        status = item.get("status", "unknown")
        error = item.get("error", "")
        return f"<!-- {kind} media not available: {name} (status={status}{f', {error}' if error else ''}) -->"

    return replace


def clean_markdown(markdown: str) -> str:
    """Remove Feishu-specific view tags and attribute markers."""
    markdown = VIEW_TAG_RE.sub("", markdown)
    # Strip inline attribute blocks like {folded="true"} that Feishu attaches to headings.
    markdown = re.sub(r"\s*\{[^}]+\}\s*$", "", markdown, flags=re.MULTILINE)
    return markdown


def extract_description(markdown: str, max_length: int = 160) -> str:
    """Build a plain-text description from the first meaningful paragraph."""
    # Remove code blocks first.
    text = re.sub(r"```[\s\S]*?```", "\n", markdown)
    text = re.sub(r"`[^`]+`", " ", text)
    # Remove HTML tags and media placeholders.
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    # Convert Markdown links/images to their text/alt.
    text = re.sub(r"!?\[([^\]]*)\]\([^)]+\)", r"\1", text)
    # Remove bold/italic markers.
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)
    # Remove list and heading markers.
    text = re.sub(r"^[\-*]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    # Strip Feishu attributes like {folded="true"}.
    text = re.sub(r"\{[^}]+\}", " ", text)
    # Collapse inline whitespace but keep paragraph boundaries.
    text = re.sub(r"[ \t]+", " ", text)

    # Rejoin broken lines into paragraphs, then pick the first substantial one.
    paragraphs: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if current:
                paragraphs.append(" ".join(current).strip())
                current = []
            continue
        current.append(stripped)
    if current:
        paragraphs.append(" ".join(current).strip())

    body_start = ""
    for para in paragraphs:
        # Skip paragraphs that are only punctuation, list markers, or very short fragments.
        cleaned = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9]", "", para)
        if len(cleaned) < 12:
            continue
        # Skip paragraphs that are only labels like "环境：" or "灰度测试方案：".
        if re.match(r"^([^：:：]+[：:：]\s*)+$", para):
            continue
        body_start = para
        break

    text = body_start or (paragraphs[0] if paragraphs else "")
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(" ", 1)[0] + "…"


def slugify(value: str, fallback: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or fallback


def build_frontmatter(title: str, description: str) -> str:
    def escape(value: str) -> str:
        value = value.replace("\\", "\\\\").replace('"', '\\"')
        return value

    description = description.replace("\n", " ").strip()
    return f'---\ntitle: "{escape(title)}"\ndescription: "{escape(description)}"\n---\n\n'


def convert_doc(doc: dict, media_lookup: dict[str, dict], base_url: str, topic: str) -> str:
    markdown = doc.get("markdown", "")
    markdown = clean_markdown(markdown)
    markdown = MEDIA_TAG_RE.sub(media_replacer(media_lookup, base_url, topic), markdown)
    title = doc.get("title", "Untitled")
    description = extract_description(markdown)
    frontmatter = build_frontmatter(title, description)
    return frontmatter + markdown.strip()


def write_mdx_files(
    content: dict,
    content_path: Path,
    out_dir: Path,
    topic: str,
    base_url: str,
) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    media_lookup = load_media_lookup(content, content_path)
    docs = content.get("docs", []) or []
    written: list[dict] = []

    for doc in docs:
        slug = slugify(doc.get("title", ""), doc.get("slug", "untitled"))
        filename = f"{slug}.mdx"
        target = out_dir / filename
        body = convert_doc(doc, media_lookup, base_url, topic)
        target.write_text(body, encoding="utf-8")
        written.append(
            {
                "title": doc.get("title", "Untitled"),
                "slug": slug,
                "path": str(target.relative_to(Path.cwd())),
                "source": doc.get("source", ""),
                "obj_token": doc.get("obj_token", ""),
            }
        )

    return written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build NEC .mdx files from Feishu content bundle.")
    parser.add_argument("--content", required=True, help="Path to content.json.")
    parser.add_argument("--out-dir", required=True, help="Directory to write .mdx files.")
    parser.add_argument("--topic", required=True, help="Content topic used for image path naming.")
    parser.add_argument(
        "--base-url",
        help="Base URL for local media references. Defaults to /images/<topic>.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    content_path = Path(args.content).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    topic = args.topic
    base_url = (args.base_url or f"/images/{topic}").rstrip("/")

    content = json.loads(content_path.read_text(encoding="utf-8"))
    written = write_mdx_files(content, content_path, out_dir, topic, base_url)

    report = {
        "ok": True,
        "out_dir": str(out_dir),
        "topic": topic,
        "base_url": base_url,
        "files": written,
        "count": len(written),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
