"""CLI entry: classify a pytest/CI failure log and emit HTML + JSON reports."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .accuracy import evaluate_samples
from .classifier import classify_log
from .findings_stub import emit_finding_stubs
from .report import write_html, write_json


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="failure_detective",
        description="将 pytest/CI 失败日志分诊为 environment / assertion / test_data / flaky_suspect。",
    )
    p.add_argument(
        "log",
        type=Path,
        nargs="?",
        default=None,
        help="失败日志文件路径（文本）。与 --self-check 二选一。",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="输出目录（默认当前目录）。写入 report.html / report.json",
    )
    p.add_argument(
        "--prefix",
        default="report",
        help="输出文件名前缀（默认 report）",
    )
    p.add_argument(
        "--rules",
        type=Path,
        default=None,
        help="自定义 rules.yaml 路径（默认使用包内规则包）",
    )
    p.add_argument(
        "--emit-finding-stub",
        action="store_true",
        help="按分类结果在 --findings-dir 写入 Markdown 发现草稿（待人工确认）",
    )
    p.add_argument(
        "--findings-dir",
        type=Path,
        default=Path("findings"),
        help="--emit-finding-stub 输出目录（默认 ./findings）",
    )
    p.add_argument(
        "--stub-limit",
        type=int,
        default=5,
        help="最多生成几条 finding stub（默认 5）",
    )
    p.add_argument(
        "--self-check",
        action="store_true",
        help="对 samples/ 标注样本做准确率自检并打印结果（面试可演示）",
    )
    p.add_argument(
        "--samples-dir",
        type=Path,
        default=None,
        help="自检样本目录（默认仓库 samples/）",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.self_check:
        samples = args.samples_dir
        if samples is None:
            samples = Path(__file__).resolve().parents[1] / "samples"
        result = evaluate_samples(samples)
        print(f"准确率自检: {result.correct}/{result.total} = {result.accuracy:.0%}")
        for name, exp, act, ok in result.details:
            mark = "OK" if ok else "MISS"
            print(f"  [{mark}] {name}: expected={exp} actual={act}")
        return 0 if result.correct == result.total else 1

    if args.log is None:
        print("错误：请提供日志路径，或使用 --self-check", file=sys.stderr)
        return 2

    log_path: Path = args.log
    if not log_path.is_file():
        print(f"错误：找不到日志文件：{log_path}", file=sys.stderr)
        return 2

    out_dir: Path = args.out if args.out is not None else Path.cwd()
    out_dir.mkdir(parents=True, exist_ok=True)

    report = classify_log(log_path, rules_path=args.rules)
    html_path = out_dir / f"{args.prefix}.html"
    json_path = out_dir / f"{args.prefix}.json"
    write_html(report, html_path)
    write_json(report, json_path)

    report.rebuild_summary()
    print(f"来源: {report.source}")
    print(f"共 {len(report.findings)} 条分诊结果")
    for cat, n in report.summary.items():
        if n:
            print(f"  - {cat}: {n}")
    print(f"HTML: {html_path.resolve()}")
    print(f"JSON: {json_path.resolve()}")

    if args.emit_finding_stub:
        paths = emit_finding_stubs(
            report, args.findings_dir, limit=args.stub_limit
        )
        print(f"Finding stubs ({len(paths)}):")
        for p in paths:
            print(f"  - {p.resolve()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
