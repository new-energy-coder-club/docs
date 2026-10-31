from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.ci.page_insights import build_record, iter_mdx_files, render_report, resolve_slug_from_rel_path


OUTPUT_DIR = ROOT / "generated"
OVERRIDES_PATH = OUTPUT_DIR / "page-insights.overrides.json"


def load_overrides(path: Path) -> dict:
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8").strip()
    return json.loads(raw or "{}")


def generate_outputs(docs_root: Path, output_dir: Path, overrides_path: Path) -> None:
    overrides = load_overrides(overrides_path)
    records: dict[str, dict] = {}

    for mdx_path in iter_mdx_files(docs_root):
        rel_path = mdx_path.relative_to(docs_root).as_posix()
        slug = resolve_slug_from_rel_path(rel_path)
        record = build_record(rel_path=rel_path, text=mdx_path.read_text(encoding="utf-8"))
        record.update(overrides.get(slug, {}))
        records[slug] = record

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "page-insights.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "page-insights-report.md").write_text(
        render_report(records),
        encoding="utf-8",
    )


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not OVERRIDES_PATH.exists():
        OVERRIDES_PATH.write_text("{}\n", encoding="utf-8")
    generate_outputs(ROOT, OUTPUT_DIR, OVERRIDES_PATH)
    print("Generated page insights at generated/page-insights.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
