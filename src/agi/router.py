# src/agi/router.py
from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, Request

# ---- AGI internal modules ----
# Compute / Device
from src.agi.compute.device import describe_device

# Memory
from src.agi.memory.persistent import list_snapshots

# Scanner (quick / full scan)
from src.agi.scanner.file_scan import QuickScanResult, FullScanResult, quick_scan, full_scan

# Health Checks
from src.agi.checks.dbcheck import run_db_checks
from src.agi.checks.api_runtime import run_api_checks, run_runtime_checks

# Code Advisor
from src.agi.coder.assistant import CodeAdvice


# ------------------------------------------------------
#  Main entry for AGI router
# ------------------------------------------------------
def get_agi_router() -> APIRouter:
    """
    Create and return the AGI FastAPI Router.
    This router is mounted in main.py under /agi.
    """
    router = APIRouter()

    # --------------------------------------------------
    # 1) Basic health
    # --------------------------------------------------
    @router.get("/device", summary="Describe compute device")
    async def get_device() -> Dict[str, Any]:
        """Return CPU/GPU detection info"""
        return {"ok": True, "component": "agi_core", "info": describe_device()}

    @router.get("/health", summary="AGI core health check")
    async def get_health() -> Dict[str, Any]:
        """Simple OK response"""
        return {"ok": True, "component": "agi_core"}

    # --------------------------------------------------
    # 2) Quick scan / Full scan
    # --------------------------------------------------
    @router.get("/scan/quick",
                response_model=QuickScanResult,
                summary="Run a lightweight project scan")
    async def agi_quick_scan() -> QuickScanResult:
        return await quick_scan()

    @router.get("/scan/full",
                response_model=FullScanResult,
                summary="Run a full project scan and optionally persist snapshot")
    async def agi_full_scan(persist: bool = True) -> FullScanResult:
        return await full_scan(persist=persist)

    # --------------------------------------------------
    # 3) List AGI memory snapshots
    # --------------------------------------------------
    @router.get("/snapshots",
                summary="List AGI scan snapshots in memory")
    async def agi_list_snapshots() -> List[Dict[str, Any]]:
        snaps = []
        for p in list_snapshots():
            snaps.append({"name": p.name, "path": str(p)})
        return snaps

    # --------------------------------------------------
    # 4) AGI DB Health Check
    # --------------------------------------------------
    @router.get("/check/db",
                summary="AGI DB health check (tables, session, schema issues)")
    async def agi_check_db() -> Dict[str, Any]:
        summary, issues = await run_db_checks()
        advice = CodeAdvice.summarize_issues(issues)
        return {
            "ok": len(issues) == 0,
            "summary": summary,
            "issues": issues,
            "advice": advice,
        }

    # --------------------------------------------------
    # 5) AGI API Surface Check
    # --------------------------------------------------
    @router.get("/check/api",
                summary="Check API surface for duplicate routes / collisions")
    async def agi_check_api(request: Request) -> Dict[str, Any]:
        result = run_api_checks(request.app)
        advice = CodeAdvice.summarize_api_report(result)
        return {
            "ok": len(result.get("duplicates", [])) == 0,
            "report": result,
            "advice": advice,
        }

    # --------------------------------------------------
    # 6) AGI Runtime Check
    # --------------------------------------------------
    @router.get("/check/runtime",
                summary="Inspect Python runtime / packages / env")
    async def agi_check_runtime() -> Dict[str, Any]:
        data = run_runtime_checks()
        advice = CodeAdvice.summarize_runtime(data)
        return {
            "ok": True,
            "runtime": data,
            "advice": advice,
        }

    # --------------------------------------------------
    # 7) Future task checks placeholder (AGI V3)
    # --------------------------------------------------
    @router.get("/check/tasks",
                summary="Placeholder for AGI task health (future V3 logic)")
    async def agi_check_tasks() -> Dict[str, Any]:
        return {
            "ok": True,
            "component": "agi_core",
            "summary": "Task-level AGI diagnostics (V3 upcoming)",
        }

    # --------------------------------------------------
    return router
