import json
from pathlib import Path

from tools.ci.check_docs import check_page_insights_artifacts
from tools.ci.generate_page_insights import generate_outputs
from tools.ci.inject_page_insights import sync_page_insights_mounts
from tools.ci.page_insights import (
    build_summary,
    classify_page_kind,
    compute_length_band,
    compute_reading_minutes,
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


def test_classify_page_kind_marks_index_for_card_heavy_index_page():
    text = """---
title: "NEC 10 日集训"
description: "overview"
---

本集训面向 NEC 2027 赛季新成员，帮助你建立机器人竞赛所需的全局认知与基础实践能力。

## 十日学习地图

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


def test_build_summary_ignores_injected_import_and_mount_lines():
    body = """
import { PageInsights } from "/snippets/page-insights.jsx";

<PageInsights />

NEC 社区面向机器人竞赛与真实工程项目，沉淀机械、视觉与嵌入式经验。

## 学习路径

从新人入门到项目实战逐步展开。
"""

    summary = build_summary(
        title="关于 NEC 社区",
        body=body,
        max_sentences=2,
    )

    assert "PageInsights" not in summary
    assert "NEC 社区面向机器人竞赛与真实工程项目" in summary


def test_resolve_slug_from_rel_path_removes_mdx_suffix():
    from tools.ci.page_insights import resolve_slug_from_rel_path

    assert resolve_slug_from_rel_path("community/about.mdx") == "community/about"


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
    assert "page-insights.jsx" not in index_text


def test_check_page_insights_artifacts_requires_generated_files(tmp_path: Path):
    errors = check_page_insights_artifacts(tmp_path)

    assert "缺少生成文件: generated/page-insights.json" in errors
    assert "缺少生成文件: generated/page-insights-report.md" in errors
    assert "缺少生成文件: generated/page-insights.overrides.json" in errors
