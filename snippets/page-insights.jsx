import insights from "/generated/page-insights.json";

export const PageInsights = () => {
  // Mintlify 代码片段运行时不支持 JSON 导入，insights 可能为未绑定标识符，
  // 必须先判空再使用，否则整页 hydration 崩溃。
  const data = typeof insights === "undefined" ? null : insights;
  if (!data) return null;

  const path =
    typeof window === "undefined"
      ? ""
      : window.location.pathname.replace(/^\/+|\/+$/g, "");
  const slug = path || "index";
  const entry = data[slug];

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
