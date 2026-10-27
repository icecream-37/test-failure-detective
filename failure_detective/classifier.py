"""Rule-based failure log classifier (offline, deterministic, demoable)."""

from __future__ import annotations

import re
from pathlib import Path

from .models import Category, Finding, Report
from .rules_loader import Rule, get_default_rules, load_rules_from_path


def _split_failure_blocks(text: str) -> list[tuple[str | None, str]]:
    """Split a pytest-style log into failure blocks with optional test names."""
    failures_match = re.search(r"^={5,}\s*FAILURES\s*={5,}\s*$", text, re.M | re.I)
    errors_match = re.search(r"^={5,}\s*ERRORS\s*={5,}\s*$", text, re.M | re.I)
    short_match = re.search(
        r"^={5,}\s*short test summary info\s*={5,}\s*$", text, re.M | re.I
    )

    body = text
    if failures_match:
        start = failures_match.end()
        end = (
            short_match.start()
            if short_match and short_match.start() > start
            else len(text)
        )
        body = text[start:end]
    elif errors_match:
        start = errors_match.end()
        end = (
            short_match.start()
            if short_match and short_match.start() > start
            else len(text)
        )
        body = text[start:end]

    # If both ERRORS and FAILURES exist and we started at FAILURES, prepend ERRORS section
    if failures_match and errors_match and errors_match.start() < failures_match.start():
        err_start = errors_match.end()
        err_end = failures_match.start()
        body = text[err_start:err_end] + "\n" + body

    parts = re.split(r"\n_{5,}\s+", body)
    blocks: list[tuple[str | None, str]] = []

    if len(parts) <= 1:
        failed_lines = re.findall(r"^(?:FAILED|ERROR)\s+(\S+.*)$", text, re.M)
        if failed_lines and len(text) < 8000:
            blocks.append((failed_lines[0].strip(), text))
        else:
            blocks.append((None, text.strip()))
        return [(n, b) for n, b in blocks if b.strip()]

    for part in parts:
        part = part.strip()
        if not part:
            continue
        first_line, _, rest = part.partition("\n")
        name = None
        m = re.match(r"^(.+?)\s+_{3,}\s*$", first_line.strip())
        if m:
            name = m.group(1).strip()
            content = rest.strip() or part
        elif "::" in first_line or first_line.startswith("test_") or first_line.startswith(
            "ERROR"
        ):
            name = first_line.strip().rstrip(" _")
            # Strip trailing underscores from pytest header leftovers
            name = re.sub(r"\s+_+$", "", name)
            content = rest.strip() or part
        else:
            content = part
        if content.strip():
            blocks.append((name, content))

    if not blocks:
        blocks.append((None, text.strip()))
    return blocks


def _evidence_snippet(block: str, match: re.Match[str], radius: int = 120) -> str:
    start = max(0, match.start() - radius)
    end = min(len(block), match.end() + radius)
    snippet = block[start:end].strip()
    snippet = re.sub(r"\s+", " ", snippet)
    if len(snippet) > 280:
        snippet = snippet[:277] + "..."
    return snippet


def _classify_block(
    test_name: str | None, block: str, rules: list[Rule] | tuple[Rule, ...]
) -> Finding:
    matches: list[tuple[Rule, re.Match[str]]] = []
    for rule in rules:
        m = rule.pattern.search(block)
        if m:
            matches.append((rule, m))

    if not matches:
        return Finding(
            category=Category.UNKNOWN,
            confidence=0.4,
            evidence=(block[:240] + "…") if len(block) > 240 else block,
            suggestion_zh="人工打开完整日志：补关键字规则，或标记后纳入下一轮规则迭代。",
            rule_id="unknown_fallback",
            test_name=test_name,
        )

    matches.sort(key=lambda rm: (-rm[0].priority, -rm[0].confidence))
    rule, m = matches[0]
    return Finding(
        category=rule.category,
        confidence=rule.confidence,
        evidence=_evidence_snippet(block, m),
        suggestion_zh=rule.suggestion_zh,
        rule_id=rule.rule_id,
        test_name=test_name,
    )


def classify_text(
    text: str,
    source: str = "<string>",
    rules: list[Rule] | tuple[Rule, ...] | None = None,
) -> Report:
    """Classify failure log text into categorized findings."""
    active = list(rules) if rules is not None else list(get_default_rules())
    blocks = _split_failure_blocks(text)
    findings = [_classify_block(name, block, active) for name, block in blocks]
    report = Report(
        source=source,
        findings=findings,
        notes_zh=(
            "规则引擎离线分类结果，建议抽检后写入 findings/*.md 归档；"
            "误报请反馈关键字以便迭代 rules.yaml。"
        ),
    )
    report.rebuild_summary()
    return report


def classify_log(
    path: str | Path,
    rules_path: str | Path | None = None,
) -> Report:
    """Read a log file and classify it."""
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="replace")
    rules = load_rules_from_path(Path(rules_path)) if rules_path else None
    return classify_text(text, source=str(p), rules=rules)
