# src/agi/memory/persistent.py
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def _project_root() -> Path:
    """
    src/agi/memory/persistent.py -> project root
    parents[0] = .../src/agi/memory
    parents[1] = .../src/agi
    parents[2] = .../src
    parents[3] = .../PROJECT_ROOT
    """
    return Path(__file__).resolve().parents[3]


def _snapshot_root() -> Path:
    """
    Runtime snapshot directory:
        <PROJECT_ROOT>/runtime/agi_snapshots
    """
    root = _project_root() / "runtime" / "agi_snapshots"
    root.mkdir(parents=True, exist_ok=True)
    return root


def list_snapshots() -> List[Path]:
    """
    List all snapshot files (JSON) in snapshot directory.
    Used by /agi/snapshots endpoint.
    """
    root = _snapshot_root()
    snaps: List[Path] = []
    for path in sorted(root.glob("*.json")):
        snaps.append(path)
    return snaps


def _safe_name(name: str) -> str:
    """
    Turn arbitrary snapshot name into a filesystem-safe slug.
    """
    allowed = []
    for ch in name:
        if ch.isalnum() or ch in ("-", "_"):
            allowed.append(ch)
        elif ch.isspace():
            allowed.append("_")
    slug = "".join(allowed).strip("_") or "snapshot"
    return slug


def save_snapshot(name: str, payload: Dict[str, Any]) -> Optional[Path]:
    """
    Persist scan result to disk as JSON.
    Errors are swallowed and None is returned (API response မှာ advice ပေးလောက်အောင်).
    """
    root = _snapshot_root()
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    fname = f"{ts}_{_safe_name(name)}.json"
    path = root / fname

    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return path
    except Exception:
        # Disk error / permission issue – API 쪽မှာ advice ပေးဖို့အတွက်
        return None
