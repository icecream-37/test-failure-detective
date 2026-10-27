"""Emit Markdown finding stubs from classification results (tester workflow)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from .models import Category, Finding, Report

_SEVERITY_HINT = {
    Category.ENVIRONMENT: "P1",
    Category.ASSERTION: "P2",
    Category.TEST_DATA: "P2",
    Category.FLAKY_SUSPECT: "P3",
    Category.UNKNOWN: "P3",
}


def _slug(text: str, max_len: int = 40) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in text.lower())
    cleaned = "-".join(p for p in cleaned.split("-") if p)
    return (cleaned or "finding")[:max_len]


def render_finding_md(
    finding: Finding,
    *,
    source: str,
    finding_id: str,
    env_zh: str = "本地 / CI（待填写）",
) -> str:
    today = date.today().isoformat()
    title = finding.test_name or finding.rule_id or "未命名失败"
    severity = _SEVERITY_HINT.get(finding.category, "P3")
    return f"""# [{finding_id}] {title}

| 字段 | 内容 |
|------|------|
| 日期 | {today} |
| 环境 | {env_zh} |
| 严重级别 | {severity}（工具建议，人工可改） |
| 状态 | 待确认 |
| 来源日志 | `{source}` |
| 工具分类 | `{finding.category.value}`（{finding.category.label_zh}） |
| 置信度 | {finding.confidence:.0%} |
| 命中规则 | `{finding.rule_id}` |

## 现象

（用一句话描述：哪个用例 / 流水线步骤失败，对发布或回归的影响。）

用例：`{finding.test_name or "（未解析）"}`

## 日志证据

```
{finding.evidence}
```

## 工具分类结果

- 类别：{finding.category.label_zh}
- 建议下一步（机器生成）：{finding.suggestion_zh}

## 人工结论

- [ ] 同意工具分类
- [ ] 纠正为：________
- [ ] 根因：（产品缺陷 / 用例过时 / 环境未就绪 / 数据问题 / Flaky / 其他）

（在此写清：你验证了什么、结论是什么。）

## 复现步骤

1. …
2. …
3. 期望：…　实际：…

## 建议

- …

## 关联

- 相关用例 / PR / Issue：
- HTML 报告：
"""


def emit_finding_stubs(
    report: Report,
    out_dir: Path,
    *,
    limit: int = 5,
    skip_unknown: bool = False,
) -> list[Path]:
    """Write one Markdown stub per top finding. Returns written paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    findings = report.findings
    if skip_unknown:
        findings = [f for f in findings if f.category != Category.UNKNOWN]
    for i, finding in enumerate(findings[:limit], 1):
        fid = f"F-{date.today().strftime('%Y%m%d')}-{i:02d}"
        name_part = _slug(finding.test_name or finding.category.value)
        path = out_dir / f"{fid}_{name_part}.md"
        # Avoid clobbering interview examples: if exists, add suffix
        if path.exists():
            path = out_dir / f"{fid}_{name_part}_{i}.md"
        path.write_text(
            render_finding_md(finding, source=report.source, finding_id=fid),
            encoding="utf-8",
        )
        written.append(path)
    return written
