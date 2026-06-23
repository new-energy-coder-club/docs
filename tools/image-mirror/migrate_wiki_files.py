#!/usr/bin/env python3
"""
Bulk migrate Feishu-exported wiki .md files to Mintlify-compatible .mdx files.
- Renames Chinese filenames to English slugs
- Adds YAML frontmatter
- Strips Feishu-specific syntax that breaks MDX rendering
"""

import io
import re
import sys
from pathlib import Path

# Force UTF-8 stdout/stderr on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

WIKI_DIR = Path(__file__).resolve().parents[2] / "wiki"

FILE_MAP = {
    "01_start-here-新人入口.md": ("start-here.mdx", "Start Here 新人入口"),
    "02_learn-学习路线.md": ("learning-path.mdx", "学习路线"),
    "03_build-项目与竞赛.md": ("projects-and-competitions.mdx", "项目与竞赛"),
    "04_contribute-参与gitee协作.md": ("gitee-contribution.mdx", "参与 Gitee 协作"),
    "05_community-社区.md": ("community.mdx", "社区"),
    "06_nec-付费会员-月付.md": ("nec-plus-membership.mdx", "NEC+ 付费会员"),
    "07_nec-培训资源中心.md": ("training-resources.mdx", "培训资源中心"),
    "08_常见q-a.md": ("faq.mdx", "常见 Q&A"),
    "09_nec-往届经验速查-框架.md": ("experience-index.mdx", "往届经验速查框架"),
    "11_nec-安全与规范索引.md": ("safety-and-standards.mdx", "安全与规范索引"),
}

# Regex patterns for Feishu-specific syntax
PATTERNS = [
    (re.compile(r'<text\s+color="[^"]*">(.*?)</text>'), r'\1'),
    (re.compile(r'<text\s+bgcolor="[^"]*">(.*?)</text>'), r'\1'),
    (re.compile(r'<mention-doc[^>]*>.*?</mention-doc>'), ''),
    (re.compile(r'<mention-user[^>]*/?>'), ''),
    (re.compile(r'<sub-page-list[^>]*/?>'), ''),
    (re.compile(r'<image[^>]*/?>'), ''),
    (re.compile(r'\{folded="true"\}'), ''),
    (re.compile(r'\{folded="false"\}'), ''),
]


def clean_feishu_syntax(text: str) -> str:
    for pattern, repl in PATTERNS:
        text = pattern.sub(repl, text)
    return text


def clean_heading_line(line: str) -> str:
    """Remove Feishu wrappers like '< ① Start Here（新人入口） >' from headings."""
    # Remove leading #s and spaces first
    match = re.match(r'^(#+\s*)(.*)$', line)
    if not match:
        return line

    prefix = match.group(1)
    content = match.group(2).strip()

    # Strip wrappers: < ① Title >  or  < Title >
    content = re.sub(r'^[<\s]*(?:[①-⑩]|\d+[\.、])?\s*', '', content)
    content = re.sub(r'\s*[>\s]*$', '', content)
    # Remove any remaining <text> tags
    content = re.sub(r'<text[^>]*>|</text>', '', content)
    content = content.strip()

    return f"{prefix}{content}" if content else ""


def clean_content(text: str) -> str:
    lines = text.splitlines()
    cleaned_lines = []

    for line in lines:
        if line.strip().startswith("#"):
            new_line = clean_heading_line(line)
            if new_line:
                cleaned_lines.append(new_line)
        else:
            cleaned_lines.append(line)

    # Remove excessive blank lines (more than 2 consecutive)
    result = []
    blank_count = 0
    for line in cleaned_lines:
        if line.strip() == "":
            blank_count += 1
            if blank_count <= 2:
                result.append(line)
        else:
            blank_count = 0
            result.append(line)

    return "\n".join(result).strip()


def extract_title_and_description(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    title = ""
    description = ""

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            title = clean_heading_line(stripped)[2:].strip()
            break

    # Use first non-empty, non-heading, non-separator paragraph as description
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("---"):
            description = stripped.lstrip(">").strip()
            if len(description) > 120:
                description = description[:117] + "..."
            break

    return title, description


def migrate_file(old_name: str, new_name: str, fallback_title: str) -> dict:
    old_path = WIKI_DIR / old_name
    new_path = WIKI_DIR / new_name

    if not old_path.exists():
        print(f"[SKIP] {old_name} not found")
        return {}

    raw_text = old_path.read_text(encoding="utf-8")
    cleaned_syntax = clean_feishu_syntax(raw_text)
    cleaned = clean_content(cleaned_syntax)

    title, description = extract_title_and_description(cleaned)
    if not title:
        title = fallback_title
    if not description:
        description = f"{title} - NEC 知识库"

    # Escape double quotes in frontmatter
    title = title.replace('"', '\\"')
    description = description.replace('"', '\\"')

    frontmatter = f"""---
title: "{title}"
description: "{description}"
---

"""

    new_path.write_text(frontmatter + cleaned + "\n", encoding="utf-8")
    old_path.unlink()

    return {
        "old": old_name,
        "new": new_name,
        "title": title,
        "slug": new_name.replace(".mdx", ""),
    }


def update_docs_json(mappings: list[dict]):
    docs_json_path = WIKI_DIR.parent / "docs.json"
    text = docs_json_path.read_text(encoding="utf-8")

    for m in mappings:
        old_slug = m["old"].replace(".md", "")
        new_slug = m["slug"]
        text = re.sub(
            rf'"wiki/{re.escape(old_slug)}(?:\.md)?"',
            f'"wiki/{new_slug}"',
            text,
        )

    docs_json_path.write_text(text, encoding="utf-8")


def update_readme(mappings: list[dict]):
    readme_path = WIKI_DIR / "README.md"
    text = readme_path.read_text(encoding="utf-8")

    for m in mappings:
        old_name = m["old"]
        new_name = m["new"]
        title = m["title"].replace('\\"', '"')
        # Replace the whole table row if found
        text = re.sub(
            rf'\|\s*\d+\s*\|\s*`{re.escape(old_name)}`\s*\|\s*[^|]+\|',
            f'| - | `{new_name}` | {title} |',
            text,
        )

    readme_path.write_text(text, encoding="utf-8")


def main():
    print(f"Migrating wiki files in {WIKI_DIR}")
    mappings = []

    for old_name, (new_name, fallback_title) in FILE_MAP.items():
        result = migrate_file(old_name, new_name, fallback_title)
        if result:
            mappings.append(result)
            print(f"[OK] {old_name} -> {new_name}")

    if mappings:
        update_docs_json(mappings)
        update_readme(mappings)
        print("\nUpdated docs.json and wiki/README.md")
        print("\nNew navigation paths:")
        for m in mappings:
            print(f'  wiki/{m["slug"]}  # {m["title"]}')


if __name__ == "__main__":
    main()
