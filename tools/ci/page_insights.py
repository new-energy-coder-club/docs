from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)
HEADING_RE = re.compile(r"^##+\s+", re.MULTILINE)
CARD_RE = re.compile(r"<Card[\s>]", re.MULTILINE)
ACCORDION_GROUP_RE = re.compile(r"<AccordionGroup[\s>]", re.MULTILINE)
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
WORD_RE = re.compile(r"[A-Za-z]{4,}")
CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
TABLE_LINE_RE = re.compile(r"^\|.*\|$", re.MULTILINE)
ENGLISH_WORD_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9_-]*\b")
H2_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
IMPORT_LINE_RE = re.compile(r'^\s*import\s+.*?from\s+["\'][^"\']+["\'];?\s*$', re.MULTILINE)
PAGE_INSIGHTS_MOUNT_RE = re.compile(r"^\s*<PageInsights\s*/>\s*$", re.MULTILINE)


@dataclass
class PageFeatures:
    rel_path: str
    title: str
    text_chars: int
    heading_count: int
    paragraph_count: int
    card_count: int
    accordion_count: int
    has_root_index_path: bool


def resolve_slug_from_rel_path(rel_path: str) -> str:
    return rel_path[:-4] if rel_path.endswith(".mdx") else rel_path


def parse_frontmatter_and_body(text: str) -> tuple[dict[str, str], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text

    raw_frontmatter = match.group(1)
    frontmatter: dict[str, str] = {}
    for line in raw_frontmatter.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip().strip('"').strip("'")

    return frontmatter, text[match.end():]


def _strip_mdx_markup(body: str) -> str:
    body = _clean_body_for_analysis(body)
    body = CODE_BLOCK_RE.sub(" ", body)
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", body)
    body = re.sub(r"\[[^\]]+\]\([^)]+\)", " ", body)
    body = re.sub(r"^\|.*\|$", " ", body, flags=re.MULTILINE)
    body = re.sub(r"\s+", " ", body)
    return body.strip()


def _clean_body_for_analysis(body: str) -> str:
    body = IMPORT_LINE_RE.sub(" ", body)
    body = PAGE_INSIGHTS_MOUNT_RE.sub(" ", body)
    return body


def compute_reading_minutes(
    text_chars: int,
    english_words: int,
    code_chars: int,
    table_chars: int,
) -> int:
    weighted_chars = text_chars + int(code_chars * 0.2) + int(table_chars * 0.5)
    chinese_minutes = weighted_chars / 300 if weighted_chars else 0
    english_minutes = english_words / 180 if english_words else 0
    minutes = int(-(-max(chinese_minutes + english_minutes, 1) // 1))
    return max(minutes, 1)


def compute_length_band(text_chars: int, reading_minutes: int) -> str:
    if text_chars < 250 or reading_minutes <= 1:
        return "short"
    if text_chars > 4500 or reading_minutes >= 15:
        return "long"
    return "normal"


def build_summary(title: str, body: str, max_sentences: int = 3) -> str:
    _ = title
    cleaned_body = _clean_body_for_analysis(body)
    body_without_code = CODE_BLOCK_RE.sub(" ", cleaned_body)
    intro_candidates = [
        line.strip()
        for line in body_without_code.splitlines()
        if line.strip() and not line.strip().startswith("#") and not line.strip().startswith("<")
    ]
    heading_candidates = [f"涵盖：{heading.strip()}" for heading in H2_RE.findall(body_without_code)[:2]]
    closing_candidates = intro_candidates[-1:] if len(intro_candidates) > 1 else []

    selected: list[str] = []
    for part in intro_candidates[:2] + heading_candidates + closing_candidates:
        if part and part not in selected:
            selected.append(part)
        if len(selected) >= max_sentences:
            break
    return " ".join(selected[:max_sentences]).strip()


def iter_mdx_files(docs_root: Path) -> list[Path]:
    ignored_roots = {".git", "node_modules", ".wrangler", ".clone-QW3VwEy", ".feishu-mdx-export"}
    files: list[Path] = []
    for path in docs_root.rglob("*.mdx"):
        if any(part in ignored_roots for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def build_record(rel_path: str, text: str) -> dict:
    frontmatter, body = parse_frontmatter_and_body(text)
    features = extract_page_features(rel_path, text)
    page_kind = classify_page_kind(features)
    english_words = len(ENGLISH_WORD_RE.findall(body))
    code_chars = sum(len(block) for block in CODE_BLOCK_RE.findall(body))
    table_chars = sum(len(line) for line in TABLE_LINE_RE.findall(body))
    reading_minutes = compute_reading_minutes(
        text_chars=features.text_chars,
        english_words=english_words,
        code_chars=code_chars,
        table_chars=table_chars,
    )
    return {
        "slug": resolve_slug_from_rel_path(rel_path),
        "filePath": rel_path,
        "title": frontmatter.get("title", ""),
        "pageKind": page_kind,
        "readingMinutes": reading_minutes,
        "lengthBand": compute_length_band(features.text_chars, reading_minutes),
        "summary": build_summary(frontmatter.get("title", ""), body, max_sentences=3) if page_kind == "article" else "",
        "stats": {
            "textChars": features.text_chars,
            "englishWords": english_words,
            "codeWeight": int(code_chars * 0.2),
            "tableWeight": int(table_chars * 0.5),
            "headingCount": features.heading_count,
            "paragraphCount": features.paragraph_count,
        },
        "signals": {
            "positive": _positive_signals(features),
            "negative": _negative_signals(features),
        },
    }


def _positive_signals(features: PageFeatures) -> list[str]:
    signals: list[str] = []
    if features.heading_count >= 2:
        signals.append("has_multiple_headings")
    if features.paragraph_count >= 2:
        signals.append("has_continuous_paragraphs")
    if features.text_chars >= 250:
        signals.append("has_meaningful_text")
    return signals


def _negative_signals(features: PageFeatures) -> list[str]:
    signals: list[str] = []
    if features.card_count >= 2:
        signals.append("card_heavy")
    if features.has_root_index_path:
        signals.append("root_index")
    if features.text_chars < 140:
        signals.append("very_short")
    return signals


def render_report(records: dict[str, dict]) -> str:
    long_pages = [slug for slug, record in records.items() if record.get("lengthBand") == "long"]
    short_pages = [slug for slug, record in records.items() if record.get("lengthBand") == "short"]
    non_articles = [
        f"- `{slug}`: {record.get('pageKind')}"
        for slug, record in records.items()
        if record.get("pageKind") != "article"
    ]

    def _section(title: str, items: list[str]) -> str:
        if not items:
            return f"## {title}\n\n- 无\n"
        return "## " + title + "\n\n" + "\n".join(f"- `{item}`" if not item.startswith("- ") else item for item in items) + "\n"

    sections = [
        "# 页面洞察报告\n",
        _section("超长页", long_pages),
        _section("超短页", short_pages),
        "## 非正文页\n\n" + ("\n".join(non_articles) if non_articles else "- 无") + "\n",
    ]
    return "\n".join(sections)


def extract_page_features(rel_path: str, text: str) -> PageFeatures:
    frontmatter, body = parse_frontmatter_and_body(text)
    plain_text = _strip_mdx_markup(body)
    paragraphs = [
        paragraph
        for paragraph in re.split(r"\n\s*\n", body)
        if CJK_RE.search(paragraph) or WORD_RE.search(paragraph)
    ]

    return PageFeatures(
        rel_path=rel_path,
        title=frontmatter.get("title", ""),
        text_chars=len(plain_text),
        heading_count=len(HEADING_RE.findall(body)),
        paragraph_count=len(paragraphs),
        card_count=len(CARD_RE.findall(body)),
        accordion_count=len(ACCORDION_GROUP_RE.findall(body)),
        has_root_index_path=rel_path == "index.mdx",
    )


def classify_page_kind(features: PageFeatures) -> str:
    if features.rel_path.startswith("snippets/") or features.has_root_index_path:
        return "landing"
    if features.rel_path.endswith("/index.mdx") and features.card_count >= 2:
        return "index"
    if features.card_count >= 2 and features.text_chars < 600:
        return "index"
    if features.heading_count >= 2 and features.paragraph_count >= 2 and features.text_chars >= 40:
        return "article"
    if features.text_chars < 80 and features.heading_count == 0:
        return "stub"
    if features.text_chars < 140:
        return "stub"
    return "index"
