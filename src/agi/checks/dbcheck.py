# src/agi/checks/dbcheck.py
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from sqlalchemy import text

from src.db.session import get_session_ctx  # our existing DB helper


Issue = Dict[str, Any]


async def run_db_checks(timeout: float = 2.0) -> Tuple[str, List[Issue]]:
    """
    Basic DB health checks.

    Returns:
        (summary, issues)

        summary: short human text
        issues: list of structured issue dicts that CodeAdvice can explain.
    """
    issues: List[Issue] = []
    summary = "Database checks not executed"

    try:
        # simple SELECT 1 ping using our main async session
        async with get_session_ctx() as db:
            result = await db.execute(text("SELECT 1"))
            row = result.scalar_one_or_none()
    except Exception as exc:  # connection / auth / migration problems
        issues.append(
            {
                "id": "db_unreachable",
                "component": "database",
                "kind": "error",
                "summary": "Database connection failed",
                "hint": (
                    "Check DATABASE_URL, that the DB is running, "
                    "and that Alembic migrations have been applied."
                ),
                "details": {"error": str(exc)},
            }
        )
        summary = "Database connection FAILED"
        return summary, issues

    if row != 1:
        issues.append(
            {
                "id": "db_ping_unexpected",
                "component": "database",
                "kind": "warning",
                "summary": "Database ping returned unexpected result",
                "hint": (
                    "Run `SELECT 1` manually against the database and make sure "
                    "ORM / engine configuration matches the real DB."
                ),
                "details": {"row": row},
            }
        )
        summary = "Database ping returned unexpected result"
    else:
        summary = "Database connectivity OK"

    return summary, issues
