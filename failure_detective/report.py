"""HTML and JSON report writers."""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

from .models import Category, Report

_CATEGORY_COLORS = {
    Category.ENVIRONMENT: "#c0392b",
    Category.ASSERTION: "#2980b9",
    Category.TEST_DATA: "#8e44ad",
    Category.FLAKY_SUSPECT: "#d68910",
    Category.UNKNOWN: "#7f8c8d",
}


def write_json(report: Report, path: Path) -> None:
    path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_html(report: Report, path: Path) -> None:
    report.rebuild_summary()
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total = len(report.findings)
    known = sum(1 for f in report.findings if f.category != Category.UNKNOWN)

    rows_summary = []
    for cat in Category:
        count = report.summary.get(cat.value, 0)
        color = _CATEGORY_COLORS[cat]
        pct = f"{(count / total * 100):.0f}%" if total else "0%"
        rows_summary.append(
            f'<div class="stat"><div class="stat-n" style="color:{color}">{count}</div>'
            f'<div class="stat-l">{html.escape(cat.label_zh)}</div>'
            f'<div class="stat-p">{pct}</div></div>'
        )

    # Simple bar chart via flex widths
    bars = []
    for cat in Category:
        count = report.summary.get(cat.value, 0)
        if not count:
            continue
        width = max(4, int(count / total * 100)) if total else 0
        color = _CATEGORY_COLORS[cat]
        bars.append(
            f'<div class="bar-row"><span class="bar-label">{html.escape(cat.label_zh)}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{width}%;background:{color}"></div></div>'
            f'<span class="bar-n">{count}</span></div>'
        )

    finding_blocks = []
    for i, f in enumerate(report.findings, 1):
        color = _CATEGORY_COLORS[f.category]
        name = html.escape(f.test_name or "（未解析到用例名）")
        evidence = html.escape(f.evidence)
        suggestion = html.escape(f.suggestion_zh)
        cat_label = html.escape(f.category.label_zh)
        conf_pct = int(round(f.confidence * 100))
        finding_blocks.append(
            f"""
            <article class="finding" id="f-{i}">
              <header>
                <span class="badge" style="background:{color}">{cat_label}</span>
                <span class="conf">置信度 {conf_pct}%</span>
                <span class="rule">规则 <code>{html.escape(f.rule_id)}</code></span>
              </header>
              <div class="conf-bar"><div class="conf-fill" style="width:{conf_pct}%;background:{color}"></div></div>
              <h3>#{i} {name}</h3>
              <h4>证据片段</h4>
              <pre>{evidence}</pre>
              <h4>建议下一步</h4>
              <p class="suggest">{suggestion}</p>
              <p class="next">确认后请写入 <code>findings/</code> 归档（可用 <code>--emit-finding-stub</code> 生成草稿）。</p>
            </article>
            """
        )

    body = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>失败日志分诊报告 — Test Failure Detective</title>
<style>
  :root {{
    --bg: #f0f2f5; --card: #fff; --text: #1a1a1a; --muted: #5c6b7a;
    --border: #e1e6eb; --accent: #1e293b;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    background: var(--bg); color: var(--text); line-height: 1.55;
  }}
  header.top {{
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    color: #fff; padding: 1.75rem 2rem;
  }}
  header.top h1 {{ margin: 0 0 0.35rem; font-size: 1.5rem; font-weight: 600; }}
  header.top p {{ margin: 0; opacity: 0.88; font-size: 0.95rem; }}
  main {{ max-width: 980px; margin: 0 auto; padding: 1.5rem; }}
  .summary {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
    gap: 0.75rem; margin-bottom: 1.25rem;
  }}
  .stat {{
    background: var(--card); border: 1px solid var(--border); border-radius: 10px;
    padding: 1rem 0.75rem; text-align: center;
  }}
  .stat-n {{ font-size: 1.75rem; font-weight: 700; }}
  .stat-l {{ font-size: 0.78rem; color: var(--muted); margin-top: 0.2rem; }}
  .stat-p {{ font-size: 0.72rem; color: var(--muted); }}
  .panel {{
    background: var(--card); border: 1px solid var(--border); border-radius: 10px;
    padding: 1rem 1.25rem; margin-bottom: 1.25rem;
  }}
  .panel h2 {{ margin: 0 0 0.75rem; font-size: 1rem; }}
  .meta {{ color: var(--muted); font-size: 0.9rem; }}
  .meta div {{ margin: 0.2rem 0; }}
  .bar-row {{ display: flex; align-items: center; gap: 0.6rem; margin: 0.35rem 0; }}
  .bar-label {{ width: 7.5rem; font-size: 0.8rem; color: var(--muted); flex-shrink: 0; }}
  .bar-track {{ flex: 1; background: #eef1f4; border-radius: 999px; height: 10px; overflow: hidden; }}
  .bar-fill {{ height: 100%; border-radius: 999px; }}
  .bar-n {{ width: 1.5rem; font-size: 0.8rem; text-align: right; }}
  .workflow {{
    background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 10px;
    padding: 1rem 1.25rem; margin-bottom: 1.25rem; font-size: 0.9rem;
  }}
  .workflow ol {{ margin: 0.4rem 0 0; padding-left: 1.25rem; }}
  .finding {{
    background: var(--card); border: 1px solid var(--border); border-radius: 10px;
    padding: 1.25rem; margin-bottom: 1rem;
  }}
  .finding header {{ display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; }}
  .badge {{ color: #fff; font-size: 0.75rem; padding: 0.2rem 0.55rem; border-radius: 999px; font-weight: 600; }}
  .conf, .rule {{ font-size: 0.8rem; color: var(--muted); }}
  .conf-bar {{ height: 4px; background: #eef1f4; border-radius: 999px; margin: 0.5rem 0 0.75rem; overflow: hidden; }}
  .conf-fill {{ height: 100%; }}
  .finding h3 {{ margin: 0.2rem 0 0.8rem; font-size: 1.05rem; }}
  .finding h4 {{ margin: 0.6rem 0 0.3rem; font-size: 0.85rem; color: var(--muted); }}
  pre {{
    background: #0f172a; color: #e2e8f0; padding: 0.85rem 1rem; border-radius: 8px;
    overflow-x: auto; font-size: 0.8rem; white-space: pre-wrap; word-break: break-word;
  }}
  .suggest {{ margin: 0; }}
  .next {{ margin: 0.6rem 0 0; font-size: 0.85rem; color: var(--muted); }}
  code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.85em; }}
  footer {{ text-align: center; color: var(--muted); font-size: 0.8rem; padding: 1.5rem; }}
</style>
</head>
<body>
  <header class="top">
    <h1>失败日志分诊报告</h1>
    <p>Test Failure Detective · 规则引擎离线分类 · 抽检后写入 findings 才算测试产出</p>
  </header>
  <main>
    <section class="summary">{"".join(rows_summary)}</section>
    <div class="panel">
      <h2>分布</h2>
      {"".join(bars) if bars else "<p class='meta'>无分诊条目</p>"}
    </div>
    <div class="workflow">
      <strong>推荐工作流</strong>
      <ol>
        <li>阅读本报告，按类别排障优先级处理（环境 &gt; 数据 &gt; 断言 &gt; flaky）。</li>
        <li>对确认的问题用模板落到 <code>findings/*.md</code>（或 CLI <code>--emit-finding-stub</code>）。</li>
        <li>抽检准确率：对照人工结论迭代 <code>rules.yaml</code>。</li>
      </ol>
    </div>
    <div class="panel meta">
      <div><strong>来源：</strong>{html.escape(report.source)}</div>
      <div><strong>条目 / 已识别：</strong>{total} / {known}</div>
      <div><strong>生成时间：</strong>{generated}</div>
      <div><strong>说明：</strong>{html.escape(report.notes_zh)}</div>
    </div>
    <section class="findings">
      {"".join(finding_blocks) if finding_blocks else "<p>未解析到失败条目。</p>"}
    </section>
  </main>
  <footer>failure_detective · 分类≠缺陷结论 · 以 findings 归档为准</footer>
</body>
</html>
"""
    path.write_text(body, encoding="utf-8")
