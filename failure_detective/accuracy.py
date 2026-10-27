"""Accuracy self-check against labeled sample expectations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .classifier import classify_log
from .models import Category

# Ground truth for demo samples (primary finding category).
LABELED_SAMPLES: dict[str, Category] = {
    "env_connection_refused.txt": Category.ENVIRONMENT,
    "assertion_failed.txt": Category.ASSERTION,
    "test_data_keyerror.txt": Category.TEST_DATA,
    "flaky_suspect.txt": Category.FLAKY_SUSPECT,
}


@dataclass
class AccuracyResult:
    total: int
    correct: int
    details: list[tuple[str, str, str, bool]]  # file, expected, actual, ok

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0


def evaluate_samples(samples_dir: Path) -> AccuracyResult:
    details: list[tuple[str, str, str, bool]] = []
    correct = 0
    for name, expected in LABELED_SAMPLES.items():
        path = samples_dir / name
        report = classify_log(path)
        actual = report.findings[0].category if report.findings else Category.UNKNOWN
        ok = actual == expected
        if ok:
            correct += 1
        details.append((name, expected.value, actual.value, ok))
    return AccuracyResult(total=len(LABELED_SAMPLES), correct=correct, details=details)
