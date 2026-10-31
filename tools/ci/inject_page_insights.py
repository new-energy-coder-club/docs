from __future__ import annotations

import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


IMPORT_LINE = 'import { PageInsights } from "/snippets/page-insights.jsx";'
MOUNT_LINE = "<PageInsights />"
FRONTMATTER_RE = re.compile(r"^(---\n[\s\S]*?\n---\n)", re.MULTILINE)
SNIPPET_IMPORT_RE = re.compile(
    r'^import\s+\{\s*PageInsights\s*\}\s+from\s+"/snippets/page-insights\.jsx";\n?',
    re.MULTILINE,
)


def sync_page_insights_mounts(docs_root: Path, insights_path: Path) -> None:
    insights = json.loads(insights_path.read_text(encoding="utf-8"))
    article_paths = {
        f"{slug}.mdx"
        for slug, entry in insights.items()
        if entry.get("pageKind") == "article"
    }

    for path in docs_root.rglob("*.mdx"):
        rel_path = path.relative_to(docs_root).as_posix()
        text = path.read_text(encoding="utf-8")
        wants_mount = rel_path in article_paths
        updated = text

        if wants_mount:
            if IMPORT_LINE not in updated:
                match = FRONTMATTER_RE.match(updated)
                if match:
                    updated = (
                        updated[:match.end()]
                        + "\n"
                        + IMPORT_LINE
                        + "\n\n"
                        + MOUNT_LINE
                        + "\n\n"
                        + updated[match.end():].lstrip("\n")
                    )
            if MOUNT_LINE not in updated:
                updated = updated.replace(IMPORT_LINE + "\n\n", IMPORT_LINE + "\n\n" + MOUNT_LINE + "\n\n", 1)
        else:
            updated = SNIPPET_IMPORT_RE.sub("", updated)
            updated = updated.replace(MOUNT_LINE + "\n\n", "").replace(MOUNT_LINE + "\n", "")

        if updated != text:
            path.write_text(updated, encoding="utf-8")


def main() -> int:
    sync_page_insights_mounts(ROOT, ROOT / "generated" / "page-insights.json")
    print("Synchronized page insight mounts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
