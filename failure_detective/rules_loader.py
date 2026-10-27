"""Load classification rules from YAML (with built-in fallback)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

from .models import Category

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - PyYAML is in requirements
    yaml = None  # type: ignore


@dataclass(frozen=True)
class Rule:
    rule_id: str
    category: Category
    pattern: re.Pattern[str]
    confidence: float
    suggestion_zh: str
    priority: int = 0


def _flags_from_str(flags: str | None) -> int:
    value = 0
    for ch in flags or "I":
        if ch == "I":
            value |= re.I
        elif ch == "M":
            value |= re.M
        elif ch == "S":
            value |= re.S
    return value


def rules_from_dicts(items: list[dict[str, Any]]) -> list[Rule]:
    out: list[Rule] = []
    for item in items:
        cat = Category(item["category"])
        out.append(
            Rule(
                rule_id=str(item["id"]),
                category=cat,
                pattern=re.compile(str(item["pattern"]), _flags_from_str(item.get("flags"))),
                confidence=float(item.get("confidence", 0.8)),
                suggestion_zh=str(item.get("suggestion_zh", "请人工复核完整日志。")),
                priority=int(item.get("priority", 0)),
            )
        )
    return out


def load_rules_from_path(path: Path) -> list[Rule]:
    if yaml is None:
        raise RuntimeError("PyYAML is required to load rules.yaml; pip install PyYAML")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return rules_from_dicts(list(data.get("rules") or []))


def load_packaged_rules() -> list[Rule]:
    """Load rules bundled next to this package."""
    # Prefer package data file
    pkg_path = Path(__file__).with_name("rules.yaml")
    if pkg_path.is_file():
        return load_rules_from_path(pkg_path)
    # Fallback via importlib.resources
    if yaml is None:
        raise RuntimeError("rules.yaml missing and PyYAML unavailable")
    ref = resources.files("failure_detective").joinpath("rules.yaml")
    data = yaml.safe_load(ref.read_text(encoding="utf-8"))
    return rules_from_dicts(list(data.get("rules") or []))


@lru_cache(maxsize=4)
def get_default_rules() -> tuple[Rule, ...]:
    return tuple(load_packaged_rules())
