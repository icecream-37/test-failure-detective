"""CLI smoke tests."""

from __future__ import annotations

from pathlib import Path

from failure_detective.cli import main

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


def test_cli_writes_reports(tmp_path: Path) -> None:
    code = main(
        [
            str(SAMPLES / "assertion_failed.txt"),
            "--out",
            str(tmp_path),
            "--prefix",
            "demo",
        ]
    )
    assert code == 0
    assert (tmp_path / "demo.html").is_file()
    assert (tmp_path / "demo.json").is_file()


def test_cli_emit_finding_stub(tmp_path: Path) -> None:
    findings_dir = tmp_path / "findings"
    code = main(
        [
            str(SAMPLES / "env_connection_refused.txt"),
            "--out",
            str(tmp_path),
            "--emit-finding-stub",
            "--findings-dir",
            str(findings_dir),
        ]
    )
    assert code == 0
    stubs = list(findings_dir.glob("F-*.md"))
    assert stubs
    text = stubs[0].read_text(encoding="utf-8")
    assert "工具分类" in text
    assert "人工结论" in text


def test_cli_self_check() -> None:
    assert main(["--self-check"]) == 0


def test_cli_missing_file(tmp_path: Path) -> None:
    code = main([str(tmp_path / "nope.txt")])
    assert code == 2
