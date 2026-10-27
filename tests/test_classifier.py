"""Self-tests: rule matching on sample pytest failure logs."""

from __future__ import annotations

from pathlib import Path

import pytest

from failure_detective.accuracy import evaluate_samples
from failure_detective.classifier import classify_log, classify_text
from failure_detective.models import Category
from failure_detective.report import write_html, write_json
from failure_detective.rules_loader import get_default_rules, load_rules_from_path

SAMPLES = Path(__file__).resolve().parents[1] / "samples"
RULES = Path(__file__).resolve().parents[1] / "failure_detective" / "rules.yaml"


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("env_connection_refused.txt", Category.ENVIRONMENT),
        ("assertion_failed.txt", Category.ASSERTION),
        ("test_data_keyerror.txt", Category.TEST_DATA),
        ("flaky_suspect.txt", Category.FLAKY_SUSPECT),
    ],
)
def test_sample_primary_category(filename: str, expected: Category) -> None:
    report = classify_log(SAMPLES / filename)
    assert report.findings, f"no findings for {filename}"
    assert report.findings[0].category == expected
    assert report.findings[0].confidence >= 0.7
    assert report.findings[0].evidence
    assert report.findings[0].suggestion_zh


def test_mixed_log_covers_main_buckets() -> None:
    report = classify_log(SAMPLES / "mixed_ci_log.txt")
    cats = {f.category for f in report.findings}
    assert Category.ENVIRONMENT in cats
    assert len(report.findings) >= 3


def test_unknown_fallback() -> None:
    report = classify_text("something opaque went wrong in the pipeline XYZ-999")
    assert len(report.findings) == 1
    assert report.findings[0].category == Category.UNKNOWN


def test_summary_counts() -> None:
    report = classify_log(SAMPLES / "assertion_failed.txt")
    report.rebuild_summary()
    assert report.summary[Category.ASSERTION.value] >= 1
    assert report.to_dict()["total"] == len(report.findings)


def test_html_and_json_writers(tmp_path: Path) -> None:
    report = classify_log(SAMPLES / "env_connection_refused.txt")
    html_path = tmp_path / "report.html"
    json_path = tmp_path / "report.json"
    write_html(report, html_path)
    write_json(report, json_path)
    html = html_path.read_text(encoding="utf-8")
    assert "失败日志分诊报告" in html
    assert "findings" in html
    assert "environment" in json_path.read_text(encoding="utf-8") or "环境" in html


def test_module_not_found_is_environment() -> None:
    text = "E   ModuleNotFoundError: No module named 'httpx'"
    report = classify_text(text)
    assert report.findings[0].category == Category.ENVIRONMENT


def test_keyerror_is_test_data() -> None:
    text = "E       KeyError: 'id'\ntests/test_create_post.py:28: KeyError"
    report = classify_text(text)
    assert report.findings[0].category == Category.TEST_DATA


def test_rules_yaml_loads() -> None:
    rules = load_rules_from_path(RULES)
    assert len(rules) >= 10
    assert get_default_rules()


def test_labeled_accuracy_perfect() -> None:
    result = evaluate_samples(SAMPLES)
    assert result.accuracy == 1.0, result.details
