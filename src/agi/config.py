# src/agi/config.py

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, validator


class AGISettings(BaseModel):
    """
    Central configuration for the DigniLife AGI.

    - Knows project root/src directories
    - Controls scan limits & modes
    - Controls compute/device behavior
    - Fully env-configurable so future cloud deploy is easy
    """

    # --- Project paths -----------------------------------------------------
    # Project root (can be overridden by DIGNILIFE_ROOT)
    root_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2])
    # src/ directory
    src_dir: Path | None = None

    # runtime + memory + logs
    runtime_dir: Path | None = None
    memory_dir: Path | None = None
    logs_dir: Path | None = None

    # --- Behavior flags ----------------------------------------------------
    # AGI must never auto-write in production by default
    allow_write: bool = Field(
        default=False,
        description="If false, AGI never mutates project files or DB directly.",
    )
    dry_run_default: bool = Field(
        default=True,
        description="If true, any mutating op should run as dry-run unless explicitly overridden.",
    )

    # high-level mode: affects how aggressive scans are
    mode: Literal["dev", "ci", "prod"] = Field(
        default="dev",
        description=(
            "AGI operating mode. "
            "dev: more verbose & experimental, "
            "ci: focused on repeatable checks, "
            "prod: safest / read-mostly."
        ),
    )

    # --- Compute behavior --------------------------------------------------
    force_device: Literal["auto", "cpu", "gpu"] = Field(
        default="auto",
        description="Preferred compute device. 'gpu' will fall back to CPU if unavailable.",
    )
    max_vram_mb: int | None = Field(
        default=None,
        description="Optional soft cap for VRAM usage, if GPU is used.",
    )

    # --- Scanning limits ---------------------------------------------------
    max_files_indexed: int = Field(
        default=80_000,
        description="Safety limit for how many files to index during a scan.",
    )
    max_issues_per_scan: int = Field(
        default=5_000,
        description="Max number of issues to accumulate in a single scan.",
    )

    # whether to attempt optional deep checks (db, tasks, runtime, coder)
    enable_dbcheck: bool = True
    enable_apicheck: bool = True
    enable_taskcheck: bool = True
    enable_runtimecheck: bool = True
    enable_coder: bool = True

    class Config:
        arbitrary_types_allowed = True

    # --- Validators --------------------------------------------------------

    @validator("mode", pre=True, always=True)
    def _read_mode_from_env(cls, v: str | None) -> str:
        env = os.getenv("AGI_MODE")
        if env:
            env = env.lower().strip()
            if env in {"dev", "ci", "prod"}:
                return env
        return v or "dev"

    @validator("root_dir", pre=True, always=True)
    def _resolve_root_dir(cls, v: str | Path | None) -> Path:
        env = os.getenv("DIGNILIFE_ROOT")
        if env:
            return Path(env).resolve()
        if v is None:
            return Path(__file__).resolve().parents[2]
        return Path(v).resolve()

    @validator("src_dir", always=True)
    def _resolve_src_dir(cls, v: Path | None, values: dict) -> Path:
        if v is not None:
            return v.resolve()
        root: Path = values["root_dir"]
        return (root / "src").resolve()

    @validator("runtime_dir", always=True)
    def _resolve_runtime_dir(cls, v: Path | None, values: dict) -> Path:
        if v is not None:
            return v.resolve()
        root: Path = values["root_dir"]
        return (root / "runtime").resolve()

    @validator("memory_dir", always=True)
    def _resolve_memory_dir(cls, v: Path | None, values: dict) -> Path:
        if v is not None:
            return v.resolve()
        runtime: Path = values["runtime_dir"]
        return (runtime / "memory" / "agi").resolve()

    @validator("logs_dir", always=True)
    def _resolve_logs_dir(cls, v: Path | None, values: dict) -> Path:
        if v is not None:
            return v.resolve()
        runtime: Path = values["runtime_dir"]
        return (runtime / "logs").resolve()


@lru_cache(maxsize=1)
def get_settings() -> AGISettings:
    """
    Return AGI settings (singleton).

    This reads environment variables only once.
    """
    return AGISettings()
