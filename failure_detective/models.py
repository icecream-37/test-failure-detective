"""Data models for classification findings and reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Category(str, Enum):
    ENVIRONMENT = "environment"
    ASSERTION = "assertion"
    TEST_DATA = "test_data"
    FLAKY_SUSPECT = "flaky_suspect"
    UNKNOWN = "unknown"

    @property
    def label_zh(self) -> str:
        return {
            Category.ENVIRONMENT: "环境 / 基础设施",
            Category.ASSERTION: "断言失败",
            Category.TEST_DATA: "测试数据 / Fixture",
            Category.FLAKY_SUSPECT: "疑似 Flaky",
            Category.UNKNOWN: "未分类",
        }[self]


@dataclass
class Finding:
    category: Category
    confidence: float
    evidence: str
    suggestion_zh: str
    rule_id: str = ""
    test_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["category"] = self.category.value
        d["category_label_zh"] = self.category.label_zh
        return d


@dataclass
class Report:
    source: str
    findings: list[Finding] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)
    notes_zh: str = ""

    def rebuild_summary(self) -> None:
        counts = {c.value: 0 for c in Category}
        for f in self.findings:
            counts[f.category.value] = counts.get(f.category.value, 0) + 1
        self.summary = counts

    def to_dict(self) -> dict[str, Any]:
        self.rebuild_summary()
        return {
            "source": self.source,
            "summary": self.summary,
            "findings": [f.to_dict() for f in self.findings],
            "notes_zh": self.notes_zh,
            "total": len(self.findings),
        }
