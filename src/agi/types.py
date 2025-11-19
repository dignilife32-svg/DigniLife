# src/agi/types.py

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Issue / problem types
# ---------------------------------------------------------------------------

class IssueSeverity(str, Enum):
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


class IssueCategory(str, Enum):
    file = "file"
    router = "router"
    db = "db"
    tasks = "tasks"
    runtime = "runtime"
    device = "device"
    config = "config"
    other = "other"


class IssueLocation(BaseModel):
    file_path: str = Field(..., description="Path relative to project root.")
    line: int | None = Field(
        default=None, description="1-based line number if available."
    )
    column: int | None = Field(
        default=None, description="1-based column number if available."
    )


class Issue(BaseModel):
    id: str = Field(..., description="Stable identifier for this issue.")
    category: IssueCategory = IssueCategory.other
    severity: IssueSeverity = IssueSeverity.info
    message: str
    hint: str | None = Field(
        default=None,
        description="Optional human-readable suggestion (Burmese/English mixed).",
    )
    location: IssueLocation | None = None
    details: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Scan stats & device info
# ---------------------------------------------------------------------------

class FileScanStats(BaseModel):
    total_files: int
    python_files: int
    routers: int
    csv_files: int
    last_scan_root: str
    truncated: bool = Field(
        default=False,
        description="True if scanner stopped early due to safety limits.",
    )


class DeviceInfo(BaseModel):
    backend: str = Field(..., description="cpu | cuda | unknown")
    name: str | None = None
    total_vram_gb: float | None = None
    capability: str | None = None
    cuda_available: bool = False
    forced_mode: str = "auto"
    notes: list[str] = Field(default_factory=list)


class ScanSummary(BaseModel):
    started_at: datetime
    finished_at: datetime
    duration_ms: int
    stats: FileScanStats
    issues_count: int


# ---------------------------------------------------------------------------
# API models
# ---------------------------------------------------------------------------

class QuickScanResult(BaseModel):
    """
    Lightweight scan result used by /agi/scan/quick.
    """

    summary: ScanSummary
    device: DeviceInfo
    issues: list[Issue] = Field(default_factory=list)


class FullScanResult(BaseModel):
    """
    Deeper scan result used by /agi/scan/full.

    V2 adds an optional `sections` dict so future db/task/runtime checks
    can attach their own summaries without breaking the API.
    """

    summary: ScanSummary
    device: DeviceInfo
    issues: list[Issue] = Field(default_factory=list)
    snapshot_path: str | None = Field(
        default=None,
        description="If the scan was persisted to disk, this is the snapshot file path.",
    )
    sections: dict[str, Any] | None = Field(
        default=None,
        description="Optional structured data for extra check groups (db, tasks, runtime...).",
    )
