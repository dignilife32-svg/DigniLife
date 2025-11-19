# src/daily/service.py
from __future__ import annotations

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy import text


async def list_tasks(db: AsyncSession, *, limit: int = 30, offset: int = 0) -> list[dict[str, any]]:
    q = text("""
        SELECT code, category, display_value_usd, expected_time_sec, user_prompt, description
        FROM daily_tasks
        WHERE is_active = TRUE
        ORDER BY display_value_usd NULLS LAST, expected_time_sec, code DESC
        LIMIT :limit OFFSET :offset
    """)
    try:
        rows = (await db.execute(q, {"limit": limit, "offset": offset})).mappings().all()
        return [dict(row) for row in rows]
    except (OperationalError, ProgrammingError):
        # Table not created/seeded yet → return an empty list but keep 200
        return []
    