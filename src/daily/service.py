# src/daily/service.py
from __future__ import annotations

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def list_tasks(db: AsyncSession, *, limit: int = 30, offset: int = 0) -> List[Dict[str, Any]]:
    q = text(
        """
        SELECT
          code, category, display_value_usd, expected_time_sec, user_prompt, description
        FROM daily_tasks
        WHERE is_active = 1
        ORDER BY display_value_usd / NULLIF(expected_time_sec, 0) DESC
        LIMIT :limit OFFSET :offset
        """
    )
    rows = (await db.execute(q, {"limit": limit, "offset": offset})).mappings().all()
    return [dict(row) for row in rows]
