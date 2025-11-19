import asyncio
from src.db.session import get_session_ctx as Ctx, q

async def main():
    async with Ctx() as db:
        rows = await db.execute(q("""
            SELECT date, code, display_value_usd, usd_cents, is_active
            FROM daily_tasks
            ORDER BY id DESC
            LIMIT 10
        """))
        print("[last 10 daily_tasks]")
        for r in rows.all():
            print(tuple(r))

        val = await db.execute(q("""
            SELECT COALESCE(SUM(usd_cents), 0)
            FROM daily_tasks
            WHERE date = DATE('now') AND is_active = 1
        """))
        cents = val.scalar() or 0
        usd = cents / 100.0
        print(f"\n[today] active usd_cents = {cents}  (≈ ${usd:,.2f})")

asyncio.run(main())
