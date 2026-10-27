from __future__ import annotations

from pathlib import Path

from failure_detective.classifier import classify_log
from failure_detective.findings_stub import emit_finding_stubs

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


def test_emit_stubs(tmp_path: Path) -> None:
    report = classify_log(SAMPLES / "flaky_suspect.txt")
    paths = emit_finding_stubs(report, tmp_path, limit=1)
    assert len(paths) == 1
    body = paths[0].read_text(encoding="utf-8")
    assert "flaky_suspect" in body or "疑似" in body
    assert "复现步骤" in body
