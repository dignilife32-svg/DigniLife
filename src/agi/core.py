# src/agi/core.py

from __future__ import annotations

from datetime import datetime
from time import perf_counter
from typing import Any

from .compute.device import describe_device
from .config import get_settings
from .memory.persistent import save_snapshot
from .scanner.file_scan import quick_scan, full_scan
from .types import (
    FullScanResult,
    Issue,
    IssueCategory,
    IssueLocation,
    IssueSeverity,
    QuickScanResult,
    ScanSummary,
)


def _build_summary(
    started_at: datetime,
    finished_at: datetime,
    stats,
    issues: list[Issue],
) -> ScanSummary:
    duration_ms = int((finished_at - started_at).total_seconds() * 1000)
    return ScanSummary(
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=duration_ms,
        stats=stats,
        issues_count=len(issues),
    )


def _safe_extend_issues(
    label: str,
    func,
    issues: list[Issue],
    sections: dict[str, Any],
) -> None:
    """
    Helper to call an optional deep-check function and merge its issues.

    The called function is expected to return either:
      - dict-like summary
      - or an object with `.summary` and `.issues` attributes

    Any exception is converted to a synthetic Issue so AGI never crashes.
    """
    settings = get_settings()
    if len(issues) >= settings.max_issues_per_scan:
        return

    try:
        result = func()
    except Exception as exc:  # pragma: no cover - safety
        issues.append(
            Issue(
                id=f"{label}_exception",
                category=IssueCategory.other,
                severity=IssueSeverity.error,
                message=f"AGI deep check '{label}' raised an exception.",
                hint="This does not affect DigniLife users, only AGI diagnostics.",
                location=IssueLocation(file_path="(agi_internal)", line=None, column=None),
                details={"error": repr(exc)},
            )
        )
        return

    # Try to detect Issue list in result
    if hasattr(result, "issues") and hasattr(result, "summary"):
        # result.issues is expected to be a list[Issue]
        extra_issues = list(getattr(result, "issues") or [])
        issues.extend(extra_issues)
        sections[label] = getattr(result, "summary")
    else:
        # treat as opaque summary dict
        sections[label] = result


def run_quick_scan() -> QuickScanResult:
    """
    Run a lightweight scan of the project:
      - file-level stats (root + src/)
      - device info
      - basic issues (missing src/, truncated scan, etc.)

    This is safe to call frequently (e.g. from an admin UI).
    """
    started_at = datetime.utcnow()
    t0 = perf_counter()

    stats, issues = quick_scan, full_scan ()
    device = describe_device()

    finished_at = datetime.utcnow()
    _ = perf_counter() - t0  # kept for potential future metrics

    summary = _build_summary(started_at, finished_at, stats, issues)

    return QuickScanResult(summary=summary, device=device, issues=issues)


def run_full_scan(*, persist: bool = True) -> FullScanResult:
    """
    Run a more complete scan.

    V2 behaviour:
      1) Always runs the file-level scanner
      2) Optionally runs deep checks for db, API routers, tasks, runtime, coder
         (if those modules exist and are enabled in settings)
      3) Collects all issues into a single list
      4) Optionally persists a JSON snapshot of the full result

    All deep checks are *best-effort* and fully isolated:
    any exception becomes an Issue, AGI never crashes the main app.
    """
    settings = get_settings()

    # 1) base file-level scan
    started_at = datetime.utcnow()
    _t0 = perf_counter()

    stats, issues = quick_scan, full_scan ()
    device = describe_device()

    sections: dict[str, Any] = {"files": stats}

    # 2) optional deep checks (lazy-import so missing modules never break)
    if settings.enable_dbcheck:
        try:
            from .dbcheck.schema_vs_models import run_dbcheck  # type: ignore
        except ImportError:
            pass
        else:
            _safe_extend_issues("db", run_dbcheck, issues, sections)

    if settings.enable_apicheck:
        try:
            from .apicheck.router_scan import run_apicheck  # type: ignore
        except ImportError:
            pass
        else:
            _safe_extend_issues("api", run_apicheck, issues, sections)

    if settings.enable_taskcheck:
        try:
            from .taskcheck.csv_check import run_taskcheck  # type: ignore
        except ImportError:
            pass
        else:
            _safe_extend_issues("tasks", run_taskcheck, issues, sections)

    if settings.enable_runtimecheck:
        try:
            from .runtimecheck.log_scan import run_runtimecheck  # type: ignore
        except ImportError:
            pass
        else:
            _safe_extend_issues("runtime", run_runtimecheck, issues, sections)

    if settings.enable_coder:
        try:
            from .coder.analyzer import run_static_coder_check  # type: ignore
        except ImportError:
            pass
        else:
            _safe_extend_issues("coder", run_static_coder_check, issues, sections)

    finished_at = datetime.utcnow()
    _ = perf_counter() - _t0  # reserve for metrics

    summary = _build_summary(started_at, finished_at, stats, issues)

    snapshot_path: str | None = None
    if persist:
        # We persist only the JSON-serializable dict; Pydantic v1/v2: use dict()
        data = {
            "summary": summary.dict(),
            "device": device.dict(),
            "issues": [i.dict() for i in issues],
            "sections": sections,
        }
        snap = save_snapshot(data, label="full_scan_v2")
        snapshot_path = str(snap)

    return FullScanResult(
        summary=summary,
        device=device,
        issues=issues,
        snapshot_path=snapshot_path,
        sections=sections or None,
    )
