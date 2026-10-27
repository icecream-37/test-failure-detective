"""Test Failure Detective — classify pytest/CI failure logs for faster triage."""

__version__ = "0.1.0"

from .classifier import classify_log, classify_text
from .models import Category, Finding, Report

__all__ = [
    "Category",
    "Finding",
    "Report",
    "classify_log",
    "classify_text",
    "__version__",
]
