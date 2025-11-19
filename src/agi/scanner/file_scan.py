# src/agi/scanner/file_scan.py
from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.agi.memory.persistent import save_snapshot


# ------------------------------------------------------
# Dataclasses / Pydantic models
# ------------------------------------------------------


@dataclass
class FileSummary:
    path: str
    size_bytes: int
    has_router: bool
    has_fastapi_app: bool
    has_todos: bool


class QuickScanResult(BaseModel):
    root: str = Field(..., description="Project root path")
    total_files: int = Field(..., description="Total files under root")
    total_py_files: int = Field(..., description="Total .py files under root")
    total_routers: int = Field(..., description="Number of files containing 'APIRouter('")
    total_services: int = Field(
        ..., description="Number of files under src/services or named service.py"
    )
    notes: List[str] = Field(default_factory=list)


class FullScanResult(QuickScanResult):
    files: List[Dict[str, Any]] = Field(
        default_factory=list, description="Per-file summaries"
    )
    persisted: bool = Field(
        False, description="Whether this scan result was saved to disk as snapshot"
    )
    snapshot_path: Optional[str] = Field(
        None, description="Filesystem path of persisted snapshot (if any)"
    )


# ------------------------------------------------------
# Helpers
# ------------------------------------------------------


def _project_root() -> Path:
    """
    Same logic as memory.persistent – keep in sync.
    """
    return Path(__file__).resolve().parents[3]


def _iter_files(root: Path) -> List[Path]:
    """
    Walk project tree (excluding .venv, runtime logs, .git, __pycache__ etc.)
    """
    ignore_dirs = {".git", ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache"}
    files: List[Path] = []

    for dirpath, dirnames, filenames in os.walk(root):
        # filter ignored dirs in-place
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]

        for fname in filenames:
            files.append(Path(dirpath) / fname)

    return files


def _analyze_file(path: Path) -> FileSummary:
    """
    Very lightweight static analysis for a single file.
    """
    text: str = ""
    try:
        if path.suffix == ".py":
            text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        text = ""

    has_router = "APIRouter(" in text
    has_fastapi_app = "FastAPI(" in text
    has_todos = "TODO" in text or "FIXME" in text

    try:
        size_bytes = path.stat().st_size
    except Exception:
        size_bytes = 0

    return FileSummary(
        path=str(path),
        size_bytes=size_bytes,
        has_router=has_router,
        has_fastapi_app=has_fastapi_app,
        has_todos=has_todos,
    )


def _scan_core() -> Dict[str, Any]:
    """
    Perform the actual scan. Synchronous helper used by both quick/full.
    """
    root = _project_root()
    all_files = _iter_files(root)
    py_files = [p for p in all_files if p.suffix == ".py"]

    file_summaries: List[FileSummary] = [_analyze_file(p) for p in py_files]

    total_routers = sum(1 for f in file_summaries if f.has_router)
    total_services = 0
    for f in file_summaries:
        # src/services/... or *service.py
        path = Path(f.path)
        if "services" in path.parts or path.name.endswith("service.py"):
            total_services += 1

    notes: List[str] = []
    notes.append(f"root={root}")
    notes.append(f"py_files_scanned={len(py_files)}")

    return {
        "root": str(root),
        "total_files": len(all_files),
        "total_py_files": len(py_files),
        "total_routers": total_routers,
        "total_services": total_services,
        "notes": notes,
        "files": [asdict(f) for f in file_summaries],
    }


# ------------------------------------------------------
# Public async API – used by router
# ------------------------------------------------------


async def quick_scan() -> QuickScanResult:
    """
    Lightweight summary only – for /agi/scan/quick.
    """
    data = _scan_core()
    return QuickScanResult(
        root=data["root"],
        total_files=data["total_files"],
        total_py_files=data["total_py_files"],
        total_routers=data["total_routers"],
        total_services=data["total_services"],
        notes=data["notes"],
    )


async def full_scan(persist: bool = True) -> FullScanResult:
    """
    Full project scan – includes per-file details and optional snapshot persist.
    """
    data = _scan_core()
    result = FullScanResult(
        root=data["root"],
        total_files=data["total_files"],
        total_py_files=data["total_py_files"],
        total_routers=data["total_routers"],
        total_services=data["total_services"],
        notes=data["notes"],
        files=data["files"],
    )

    if persist:
        snapshot_payload: Dict[str, Any] = result.dict()
        path = save_snapshot("full_scan", snapshot_payload)
        if path is not None:
            result.persisted = True
            result.snapshot_path = str(path)

    return result
