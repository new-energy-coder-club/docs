# Page Insights Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a static page-insights pipeline that classifies MDX pages, computes reading time, generates summaries and reports, and renders page-level insights on article pages only.

**Architecture:** Add a Python build-time generator under `tools/ci/` that scans `.mdx` files and writes `generated/page-insights.json` plus a human-readable report. Render the metadata through a reusable `snippets/page-insights.jsx` component and a batch injector script that mounts the snippet only on pages classified as `article`, keeping generated content out of source prose.

**Tech Stack:** Python 3.12, existing `tools/ci` scripts, MDX, Mintlify snippets, CSS in `style.css`, GitHub Actions docs check

---

## File Structure

### New files

- `tools/ci/page_insights.py`
  - Shared parser and scoring helpers for MDX classification, reading-time estimation, and summary generation.
- `tools/ci/generate_page_insights.py`
  - CLI entrypoint that scans pages and writes generated JSON plus the Markdown report.
- `tools/ci/inject_page_insights.py`
  - Batch injector that adds the snippet import and mount to article pages only, and removes them from non-article pages when re-run.
- `tests/tools/ci/test_page_insights.py`
  - Unit tests for classification, summary extraction, reading-time logic, report generation, and injector behavior.
- `generated/page-insights.overrides.json`
  - Manual override file committed to the repo, initially empty.
- `snippets/page-insights.jsx`
  - Runtime component that reads generated metadata for the current slug and renders the compact insight box.

### Modified files

- `style.css`
  - Add a compact page-insights visual block consistent with the existing dark theme.
- `tools/ci/check_docs.py`
  - Validate generated files exist and that injected article pages reference the snippet consistently.
- `.github/workflows/docs-check.yml`
  - Generate page insights before running docs health checks.
- `.gitignore`
  - Keep the generated report tracked or ignored deliberately; the JSON should stay tracked, while transient artifacts stay ignored if added.
- `docs/superpowers/specs/2026-08-17-page-insights-design.md`
  - No implementation edits expected; read-only reference during execution.

### Generated outputs

- `generated/page-insights.json`
- `generated/page-insights-report.md`

---

### Task 1: Build The Parsing And Classification Core

**Files:**
- Create: `tools/ci/page_insights.py`
- Test: `tests/tools/ci/test_page_insights.py`

- [ ] **Step 1: Write the failing tests for page kind classification and content extraction**

```python
from pathlib import Path

from tools.ci.page_insights import (
    PageInsightRecord,
    classify_page_kind,
    extract_page_features,
    parse_frontmatter_and_body,
)


def test_parse_frontmatter_and_body_splits_mdx_document():
    text = """---
title: "Community"
description: "About page"
toc: false
---

## Intro

NEC community intro paragraph.
"""

    frontmatter, body = parse_frontmatter_and_body(text)

    assert frontmatter["title"] == "Community"
    assert frontmatter["description"] == "About page"
    assert "## Intro" in body


def test_classify_page_kind_marks_article_when_text_dominates():
    text = """---
title: "关于 NEC 社区"
description: "intro"
toc: false
---

## 社区起源

NEC 社区成立于常州工学院，围绕机器人竞赛沉淀工程实践经验。

## 核心价值

我们强调开源、新手友好与工程实践。
"""

    features = extract_page_features("community/about.mdx", text)

    assert classify_page_kind(features) == "article"


def test_classify_page_kind_marks_index_when_cards_dominate():
    text = """---
title: "NEC 10 日集训"
description: "overview"
---

<CardGroup cols={2}>
  <Card title="Day 1" href="/training/day01-onboarding">Desc</Card>
  <Card title="Day 2" href="/training/day02-mechanical-basics">Desc</Card>
</CardGroup>
"""

    features = extract_page_features("training/index.mdx", text)

    assert classify_page_kind(features) == "index"


def test_classify_page_kind_marks_stub_for_tiny_page():
    text = """---
title: "维护者"
description: "short page"
---

联系人列表。
"""

    features = extract_page_features("community/maintainers.mdx", text)

    assert classify_page_kind(features) == "stub"
```

- [ ] **Step 2: Run the tests to verify the module does not exist yet**

Run:

```bash
python -m pytest tests/tools/ci/test_page_insights.py -k "classify or parse" -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tools.ci.page_insights'`

- [ ] **Step 3: Write the minimal parsing and classification implementation**

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)
HEADING_RE = re.compile(r"^##+\s+", re.MULTILINE)
CARD_GROUP_RE = re.compile(r"<CardGroup[\s>]", re.MULTILINE)
CARD_RE = re.compile(r"<Card[\s>]", re.MULTILINE)
ACCORDION_GROUP_RE = re.compile(r"<AccordionGroup[\s>]", re.MULTILINE)
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


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


def parse_frontmatter_and_body(text: str) -> tuple[dict[str, str], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    raw = match.group(1)
    frontmatter: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip().strip('"').strip("'")
    return frontmatter, text[match.end():]


def _strip_mdx_markup(body: str) -> str:
    body = re.sub(r"```[\s\S]*?```", " ", body)
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", body)
    body = re.sub(r"\[[^\]]+\]\([^)]+\)", " ", body)
    body = re.sub(r"^\|.*\|$", " ", body, flags=re.MULTILINE)
    body = re.sub(r"\s+", " ", body)
    return body.strip()


def extract_page_features(rel_path: str, text: str) -> PageFeatures:
    frontmatter, body = parse_frontmatter_and_body(text)
    plain_text = _strip_mdx_markup(body)
    paragraphs = [p for p in re.split(r"\n\s*\n", body) if CJK_RE.search(p) or re.search(r"[A-Za-z]{4,}", p)]
    title = frontmatter.get("title", "")
    return PageFeatures(
        rel_path=rel_path,
        title=title,
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
    if features.text_chars < 80 and features.heading_count == 0:
        return "stub"
    if features.card_count >= 2 and features.text_chars < 600:
        return "index"
    if features.heading_count >= 2 and features.paragraph_count >= 2 and features.text_chars >= 180:
        return "article"
    if features.text_chars < 250:
        return "stub"
    return "index"
```

- [ ] **Step 4: Run the focused tests and confirm they pass**

Run:

```bash
python -m pytest tests/tools/ci/test_page_insights.py -k "classify or parse" -q
```

Expected: PASS with `4 passed`

- [ ] **Step 5: Commit the parsing core**

```bash
git add tools/ci/page_insights.py tests/tools/ci/test_page_insights.py
git commit -m "feat: add page insight classification core"
```

---

### Task 2: Add Reading Time, Length Bands, And Summary Generation

**Files:**
- Modify: `tools/ci/page_insights.py`
- Modify: `tests/tools/ci/test_page_insights.py`

- [ ] **Step 1: Add failing tests for reading time, length bands, and summaries**

```python
from tools.ci.page_insights import (
    build_summary,
    compute_length_band,
    compute_reading_minutes,
)


def test_compute_reading_minutes_weights_code_and_tables_lightly():
    minutes = compute_reading_minutes(
        text_chars=900,
        english_words=60,
        code_chars=300,
        table_chars=240,
    )

    assert minutes == 4


def test_compute_length_band_marks_short_and_long():
    assert compute_length_band(text_chars=120, reading_minutes=1) == "short"
    assert compute_length_band(text_chars=5200, reading_minutes=16) == "long"
    assert compute_length_band(text_chars=900, reading_minutes=3) == "normal"


def test_build_summary_uses_intro_headings_and_conclusion():
    body = """
NEC 社区面向机器人竞赛与真实工程项目，沉淀机械、视觉与嵌入式经验。

## 学习路径

从新人入门到项目实战逐步展开。

## 社区支持

社区提供文档、导师和答疑。

总结来看，本文帮助新人快速了解站点重点内容。
"""

    summary = build_summary(
        title="关于 NEC 社区",
        body=body,
        max_sentences=3,
    )

    assert "NEC 社区面向机器人竞赛与真实工程项目" in summary
    assert "学习路径" in summary or "社区支持" in summary
```

- [ ] **Step 2: Run the focused tests to verify the new APIs are missing**

Run:

```bash
python -m pytest tests/tools/ci/test_page_insights.py -k "reading or summary or length_band" -q
```

Expected: FAIL with `ImportError` or `AttributeError` for the new functions

- [ ] **Step 3: Implement the reading-time and summary helpers**

```python
SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？.!?])\s+")
CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
TABLE_LINE_RE = re.compile(r"^\|.*\|$", re.MULTILINE)
ENGLISH_WORD_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9_-]*\b")
H2_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


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
    body_without_code = CODE_BLOCK_RE.sub(" ", body)
    intro_candidates = [
        line.strip()
        for line in body_without_code.splitlines()
        if line.strip() and not line.strip().startswith("#") and not line.strip().startswith("<")
    ]
    heading_candidates = [f"涵盖：{heading.strip()}" for heading in H2_RE.findall(body_without_code)[:2]]
    closing_candidates = intro_candidates[-1:] if len(intro_candidates) > 1 else []
    selected = []
    for part in intro_candidates[:2] + heading_candidates + closing_candidates:
        if part and part not in selected:
            selected.append(part)
        if len(selected) >= max_sentences:
            break
    return " ".join(selected[:max_sentences]).strip()
```

- [ ] **Step 4: Run the focused tests and confirm they pass**

Run:

```bash
python -m pytest tests/tools/ci/test_page_insights.py -k "reading or summary or length_band" -q
```

Expected: PASS with `3 passed`

- [ ] **Step 5: Commit the content scoring layer**

```bash
git add tools/ci/page_insights.py tests/tools/ci/test_page_insights.py
git commit -m "feat: add page insight scoring helpers"
```

---

### Task 3: Generate JSON And Markdown Reports

**Files:**
- Create: `tools/ci/generate_page_insights.py`
- Modify: `tools/ci/page_insights.py`
- Modify: `tests/tools/ci/test_page_insights.py`
- Create: `generated/page-insights.overrides.json`

- [ ] **Step 1: Add failing tests for generator output and overrides**

```python
import json
from pathlib import Path

from tools.ci.generate_page_insights import generate_outputs


def test_generate_outputs_writes_json_and_report(tmp_path: Path):
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    (docs_root / "community").mkdir()
    (docs_root / "community" / "about.mdx").write_text(
        """---
title: "关于 NEC 社区"
description: "intro"
---

## 社区起源

NEC 社区面向机器人竞赛与真实工程项目。

## 社区支持

社区提供文档和答疑支持。
""",
        encoding="utf-8",
    )
    output_dir = docs_root / "generated"
    overrides_path = output_dir / "page-insights.overrides.json"
    output_dir.mkdir()
    overrides_path.write_text("{}", encoding="utf-8")

    generate_outputs(docs_root=docs_root, output_dir=output_dir, overrides_path=overrides_path)

    data = json.loads((output_dir / "page-insights.json").read_text(encoding="utf-8"))
    report = (output_dir / "page-insights-report.md").read_text(encoding="utf-8")

    assert data["community/about"]["pageKind"] == "article"
    assert data["community/about"]["readingMinutes"] >= 1
    assert "## 超长页" in report
    assert "community/about" in report


def test_generate_outputs_applies_manual_override(tmp_path: Path):
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    (docs_root / "page.mdx").write_text(
        """---
title: "Page"
description: "desc"
---

This page is short.
""",
        encoding="utf-8",
    )
    output_dir = docs_root / "generated"
    output_dir.mkdir()
    overrides_path = output_dir / "page-insights.overrides.json"
    overrides_path.write_text(
        '{"page":{"pageKind":"article","summary":"人工摘要","hideReadingTime":true}}',
        encoding="utf-8",
    )

    generate_outputs(docs_root=docs_root, output_dir=output_dir, overrides_path=overrides_path)

    data = json.loads((output_dir / "page-insights.json").read_text(encoding="utf-8"))
    assert data["page"]["summary"] == "人工摘要"
    assert data["page"]["hideReadingTime"] is True
    assert data["page"]["pageKind"] == "article"
```

- [ ] **Step 2: Run the focused tests to verify the generator entrypoint is missing**

Run:

```bash
python -m pytest tests/tools/ci/test_page_insights.py -k "generate_outputs or manual_override" -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tools.ci.generate_page_insights'`

- [ ] **Step 3: Implement the generator CLI and empty overrides file**

```python
from __future__ import annotations

import json
from pathlib import Path

from tools.ci.page_insights import build_record, iter_mdx_files, render_report


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "generated"
OVERRIDES_PATH = OUTPUT_DIR / "page-insights.overrides.json"


def load_overrides(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8") or "{}")


def generate_outputs(docs_root: Path, output_dir: Path, overrides_path: Path) -> None:
    overrides = load_overrides(overrides_path)
    records = {}
    for mdx_path in iter_mdx_files(docs_root):
        rel_path = mdx_path.relative_to(docs_root).as_posix()
        slug = rel_path[:-4]
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
```

Create `generated/page-insights.overrides.json`:

```json
{}
```

- [ ] **Step 4: Run the focused tests and then the real generator**

Run:

```bash
python -m pytest tests/tools/ci/test_page_insights.py -k "generate_outputs or manual_override" -q
python tools/ci/generate_page_insights.py
```

Expected:

- `pytest` reports PASS
- generator prints `Generated page insights at generated/page-insights.json`

- [ ] **Step 5: Commit the generator layer**

```bash
git add tools/ci/page_insights.py tools/ci/generate_page_insights.py tests/tools/ci/test_page_insights.py generated/page-insights.overrides.json generated/page-insights.json generated/page-insights-report.md
git commit -m "feat: generate page insights metadata"
```

---

### Task 4: Add The Runtime Snippet And Visual Styling

**Files:**
- Create: `snippets/page-insights.jsx`
- Modify: `style.css`
- Test: `tests/tools/ci/test_page_insights.py`

- [ ] **Step 1: Add failing tests for runtime slug lookup and render guards**

```python
from tools.ci.page_insights import resolve_slug_from_rel_path


def test_resolve_slug_from_rel_path_removes_mdx_suffix():
    assert resolve_slug_from_rel_path("community/about.mdx") == "community/about"
```

Also prepare a manual browser verification checklist in the test file docstring:

```python
"""
Manual UI checks after snippet wiring:
1. Article page shows the page-insights block below the title.
2. Landing and index pages do not render the block.
3. Long pages show the extra hint line.
4. Hidden reading time from overrides removes the meta row.
"""
```

- [ ] **Step 2: Run the focused tests to confirm the helper is missing**

Run:

```bash
python -m pytest tests/tools/ci/test_page_insights.py -k "resolve_slug" -q
```

Expected: FAIL with `ImportError` or `AttributeError`

- [ ] **Step 3: Implement the snippet and styling**

Create `snippets/page-insights.jsx`:

```jsx
import insights from "/generated/page-insights.json";

const inferSlug = () => {
  if (typeof window === "undefined") return "";
  const path = window.location.pathname.replace(/^\/+|\/+$/g, "");
  return path || "index";
};

export const PageInsights = () => {
  const slug = inferSlug();
  const entry = insights[slug];

  if (!entry || entry.pageKind !== "article") return null;

  const showReadingTime = !entry.hideReadingTime && typeof entry.readingMinutes === "number";
  const hint =
    entry.lengthBand === "long"
      ? "本文较长，建议先看摘要再按目录阅读。"
      : entry.lengthBand === "short"
        ? "本文内容较短，适合作为索引或补充说明。"
        : "";

  return (
    <section className="page-insights" data-length-band={entry.lengthBand}>
      {showReadingTime ? (
        <div className="page-insights-meta">预计阅读 {entry.readingMinutes} 分钟</div>
      ) : null}
      {!entry.hideSummary && entry.summary ? (
        <p className="page-insights-summary">{entry.summary}</p>
      ) : null}
      {hint ? <p className="page-insights-hint">{hint}</p> : null}
    </section>
  );
};

export default PageInsights;
```

Append to `style.css`:

```css
.page-insights {
  margin: 0.75rem 0 1.25rem;
  padding: 0.9rem 1rem;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.02);
}

.page-insights-meta {
  margin-bottom: 0.45rem;
  color: var(--text-tertiary);
  font-size: 0.85rem;
  letter-spacing: 0.01em;
}

.page-insights-summary,
.page-insights-hint {
  margin: 0;
  color: var(--text-secondary);
}

.page-insights-hint {
  margin-top: 0.45rem;
  color: var(--text-tertiary);
  font-size: 0.92rem;
}
```

- [ ] **Step 4: Run tests and manually verify in Mintlify**

Run:

```bash
python -m pytest tests/tools/ci/test_page_insights.py -k "resolve_slug" -q
mint dev
```

Expected:

- `pytest` reports PASS
- In the browser, article pages display the block below the title
- Index and landing pages do not display the block

- [ ] **Step 5: Commit the runtime presentation layer**

```bash
git add snippets/page-insights.jsx style.css tests/tools/ci/test_page_insights.py
git commit -m "feat: render page insights snippet"
```

---

### Task 5: Batch Inject The Snippet Onto Article Pages

**Files:**
- Create: `tools/ci/inject_page_insights.py`
- Modify: `tests/tools/ci/test_page_insights.py`

- [ ] **Step 1: Add failing tests for idempotent injection and cleanup**

```python
from pathlib import Path

from tools.ci.inject_page_insights import sync_page_insights_mounts


def test_sync_page_insights_mounts_injects_article_and_skips_index(tmp_path: Path):
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    generated = docs_root / "generated"
    generated.mkdir()
    (generated / "page-insights.json").write_text(
        """
{
  "community/about": {"pageKind": "article"},
  "training/index": {"pageKind": "index"}
}
""".strip(),
        encoding="utf-8",
    )
    community = docs_root / "community"
    training = docs_root / "training"
    community.mkdir()
    training.mkdir()
    (community / "about.mdx").write_text(
        """---
title: "About"
description: "desc"
---

## Intro

Body
""",
        encoding="utf-8",
    )
    (training / "index.mdx").write_text(
        """---
title: "Index"
description: "desc"
---

<CardGroup cols={2}></CardGroup>
""",
        encoding="utf-8",
    )

    sync_page_insights_mounts(docs_root, generated / "page-insights.json")

    article_text = (community / "about.mdx").read_text(encoding="utf-8")
    index_text = (training / "index.mdx").read_text(encoding="utf-8")

    assert 'import { PageInsights } from "/snippets/page-insights.jsx";' in article_text
    assert "<PageInsights />" in article_text
    assert 'page-insights.jsx' not in index_text
```

- [ ] **Step 2: Run the focused tests to verify the injector is missing**

Run:

```bash
python -m pytest tests/tools/ci/test_page_insights.py -k "sync_page_insights_mounts" -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tools.ci.inject_page_insights'`

- [ ] **Step 3: Implement the injector**

```python
from __future__ import annotations

import json
import re
from pathlib import Path


IMPORT_LINE = 'import { PageInsights } from "/snippets/page-insights.jsx";'
MOUNT_LINE = "<PageInsights />"
FRONTMATTER_RE = re.compile(r"^(---\n[\s\S]*?\n---\n)", re.MULTILINE)
SNIPPET_IMPORT_RE = re.compile(r'^import\s+\{\s*PageInsights\s*\}\s+from\s+"/snippets/page-insights\.jsx";\n?', re.MULTILINE)


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
                    updated = updated[:match.end()] + "\n" + IMPORT_LINE + "\n\n" + MOUNT_LINE + "\n\n" + updated[match.end():].lstrip("\n")
            if MOUNT_LINE not in updated:
                updated = updated.replace(IMPORT_LINE + "\n\n", IMPORT_LINE + "\n\n" + MOUNT_LINE + "\n\n", 1)
        else:
            updated = SNIPPET_IMPORT_RE.sub("", updated)
            updated = updated.replace(MOUNT_LINE + "\n\n", "").replace(MOUNT_LINE + "\n", "")

        if updated != text:
            path.write_text(updated, encoding="utf-8")
```

- [ ] **Step 4: Run the focused tests and the real injector**

Run:

```bash
python -m pytest tests/tools/ci/test_page_insights.py -k "sync_page_insights_mounts" -q
python tools/ci/inject_page_insights.py
```

Expected:

- `pytest` reports PASS
- injector updates only article pages and remains idempotent on a second run

- [ ] **Step 5: Commit the mount synchronization script**

```bash
git add tools/ci/inject_page_insights.py tests/tools/ci/test_page_insights.py
git commit -m "feat: sync page insights mounts"
```

---

### Task 6: Wire The Pipeline Into CI And Local Checks

**Files:**
- Modify: `tools/ci/check_docs.py`
- Modify: `.github/workflows/docs-check.yml`
- Modify: `.gitignore`

- [ ] **Step 1: Add failing tests for generated file validation**

Add this test:

```python
from pathlib import Path

from tools.ci.check_docs import check_page_insights_artifacts


def test_check_page_insights_artifacts_requires_generated_files(tmp_path: Path):
    errors = check_page_insights_artifacts(tmp_path)
    assert "缺少生成文件: generated/page-insights.json" in errors
    assert "缺少生成文件: generated/page-insights-report.md" in errors
```

- [ ] **Step 2: Run the focused tests to verify the validation hook is missing**

Run:

```bash
python -m pytest tests/tools/ci/test_page_insights.py -k "page_insights_artifacts" -q
```

Expected: FAIL with `ImportError` or `AttributeError`

- [ ] **Step 3: Add CI generation and validation**

Append to `tools/ci/check_docs.py`:

```python
def check_page_insights_artifacts(root: Path) -> list[str]:
    errors: list[str] = []
    for rel_path in (
        "generated/page-insights.json",
        "generated/page-insights-report.md",
        "generated/page-insights.overrides.json",
    ):
        if not (root / rel_path).is_file():
            errors.append(f"缺少生成文件: {rel_path}")
    return errors
```

Then call it from `main()` alongside the existing checks:

```python
errors.extend(check_page_insights_artifacts(ROOT))
```

Modify `.github/workflows/docs-check.yml`:

```yaml
      - name: Generate page insights
        run: python tools/ci/generate_page_insights.py

      - name: Sync page insights mounts
        run: python tools/ci/inject_page_insights.py

      - name: Run docs health check
        run: python tools/ci/check_docs.py
```

Update `.gitignore` only if needed:

```gitignore
# page insights keeps canonical JSON and overrides tracked; ignore nothing else here
```

- [ ] **Step 4: Run tests and the full docs check locally**

Run:

```bash
python -m pytest tests/tools/ci/test_page_insights.py -q
python tools/ci/generate_page_insights.py
python tools/ci/inject_page_insights.py
python tools/ci/check_docs.py
```

Expected:

- `pytest` reports PASS
- generator and injector complete without errors
- docs check exits successfully

- [ ] **Step 5: Commit the CI integration**

```bash
git add tools/ci/check_docs.py .github/workflows/docs-check.yml .gitignore tests/tools/ci/test_page_insights.py
git commit -m "ci: validate page insights artifacts"
```

---

### Task 7: Manual QA On Representative Pages

**Files:**
- Modify: `generated/page-insights.overrides.json` if needed
- Verify: `community/about.mdx`
- Verify: `training/index.mdx`
- Verify: `ai-tools/isaac-gym-rl-tutorial.mdx`
- Verify: `community/maintainers.mdx`

- [ ] **Step 1: Start the local docs server**

Run:

```bash
mint dev
```

Expected: local Mintlify preview URL is available

- [ ] **Step 2: Verify one article, one index, one long page, and one stub page**

Check these pages in the browser:

- `http://localhost:3000/community/about`
- `http://localhost:3000/training`
- `http://localhost:3000/ai-tools/isaac-gym-rl-tutorial`
- `http://localhost:3000/community/maintainers`

Expected:

- `community/about` shows summary + reading time below the title
- `training/index` shows no page-insights block
- `isaac-gym-rl-tutorial` shows the long-page hint
- `community/maintainers` shows no page-insights block

- [ ] **Step 3: Adjust overrides only if classification or summary is clearly wrong**

Edit `generated/page-insights.overrides.json` like this only for concrete problems:

```json
{
  "community/about": {
    "summary": "NEC 社区介绍页，说明社区起源、核心价值、组织结构与学习交流方式。"
  }
}
```

- [ ] **Step 4: Re-run generation after override changes**

Run:

```bash
python tools/ci/generate_page_insights.py
python tools/ci/inject_page_insights.py
python tools/ci/check_docs.py
```

Expected: all commands succeed and the corrected override is visible in the browser

- [ ] **Step 5: Commit the QA-approved outputs**

```bash
git add generated/page-insights.overrides.json generated/page-insights.json generated/page-insights-report.md
git commit -m "docs: finalize page insights metadata"
```

---

## Self-Review

### Spec coverage

- Page classification: covered in Task 1
- Reading time and length bands: covered in Task 2
- Generated JSON and report: covered in Task 3
- Runtime rendering below the title: covered in Task 4 and Task 5
- Manual overrides: covered in Task 3 and Task 7
- CI and repeatable generation: covered in Task 6
- Long/short page QA: covered in Task 7

### Placeholder scan

- No `TBD`, `TODO`, or “implement later” placeholders remain
- Each coding step includes concrete file paths, code blocks, commands, and expected outcomes
- The only conditional branch is the override edit in Task 7, and the exact JSON shape is provided

### Type consistency

- `pageKind`, `readingMinutes`, `lengthBand`, `summary`, `hideReadingTime`, and `hideSummary` are used consistently across generator, overrides, and runtime snippet
- `generate_outputs()` and `sync_page_insights_mounts()` are named consistently in tests and implementation steps

