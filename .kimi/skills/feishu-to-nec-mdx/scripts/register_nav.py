#!/usr/bin/env python3
"""Register generated .mdx pages in docs.json navigation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_docs_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_docs_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def find_tab(navigation: dict, tab_name: str) -> dict | None:
    for tab in navigation.get("tabs", []):
        if tab.get("tab") == tab_name:
            return tab
    return None


def find_group(groups: list[dict], group_name: str) -> dict | None:
    for group in groups:
        if group.get("group") == group_name:
            return group
        # Recurse into nested groups (pages may contain group dicts).
        if "pages" in group:
            for page in group.get("pages", []):
                if isinstance(page, dict) and "group" in page:
                    found = find_group([page], group_name)
                    if found:
                        return found
    return None


def add_pages_to_target(target: dict, pages: list[str]) -> list[str]:
    """Add page paths to target['pages'], skipping duplicates. Returns added paths."""
    existing: list[str] = []
    if "pages" not in target or target["pages"] is None:
        target["pages"] = []

    for entry in target["pages"]:
        if isinstance(entry, str):
            existing.append(entry)
        elif isinstance(entry, dict) and "group" in entry:
            existing.append(entry.get("group", ""))

    added: list[str] = []
    for page in pages:
        if page in existing:
            continue
        target["pages"].append(page)
        existing.append(page)
        added.append(page)
    return added


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Register pages in docs.json navigation.")
    parser.add_argument("--docs-json", required=True, help="Path to docs.json.")
    parser.add_argument("--tab", required=True, help="Target tab name.")
    parser.add_argument("--group", help="Target group name. If omitted, pages go directly under the tab.")
    parser.add_argument("--pages", nargs="+", required=True, help="Page paths to register (without .mdx extension).")
    parser.add_argument("--icon", default="file-lines", help="Icon for newly created group.")
    parser.add_argument(
        "--create-group",
        action="store_true",
        help="Create the group if it does not exist under the tab.",
    )
    parser.add_argument(
        "--insert-after",
        help="Insert pages after this existing page path or group name. By default append.",
    )
    return parser.parse_args()


def insert_after(pages: list[Any], insert_pages: list[str], after: str | None) -> list[Any]:
    if not after:
        return pages + insert_pages
    try:
        index = -1
        for i, entry in enumerate(pages):
            key = entry if isinstance(entry, str) else entry.get("group", "")
            if key == after:
                index = i
                break
        if index == -1:
            return pages + insert_pages
        return pages[: index + 1] + insert_pages + pages[index + 1 :]
    except Exception:
        return pages + insert_pages


def main() -> int:
    args = parse_args()
    docs_path = Path(args.docs_json).expanduser().resolve()
    data = load_docs_json(docs_path)
    navigation = data.get("navigation")
    if not isinstance(navigation, dict):
        print("ERROR: docs.json missing navigation object.", file=sys.stderr)
        return 1

    tab = find_tab(navigation, args.tab)
    if not tab:
        print(f"ERROR: tab '{args.tab}' not found in docs.json.", file=sys.stderr)
        return 1

    target: dict | None = tab
    if args.group:
        groups = tab.get("groups", []) or []
        group = find_group(groups, args.group)
        if not group:
            if args.create_group:
                group = {"group": args.group, "icon": args.icon, "pages": []}
                groups.append(group)
                tab["groups"] = groups
            else:
                print(f"ERROR: group '{args.group}' not found under tab '{args.tab}'.", file=sys.stderr)
                return 1
        target = group

    pages = list(dict.fromkeys(args.pages))  # dedupe while preserving order
    if args.insert_after:
        target["pages"] = insert_after(target.get("pages", []), pages, args.insert_after)
        added = pages
    else:
        added = add_pages_to_target(target, pages)

    save_docs_json(docs_path, data)
    print(
        json.dumps(
            {"ok": True, "tab": args.tab, "group": args.group, "added": added},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
