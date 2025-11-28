#backfill_today_usd_cents.py
import asyncio
from src.db.session import get_session_ctx as Ctx, q

# နောက်ဆုံးရက်ကို target လုပ်မယ် (UTC/local မကြာသေး)
SQL_TARGET_DATE = q("SELECT MAX(date) FROM daily_tasks")

SQL_BACKFILL_RANDOM = q("""
    UPDATE daily_tasks
    SET display_value_usd = ROUND( (ABS(RANDOM()) % 900 + 100) / 100.0, 2 )
    WHERE date = (SELECT MAX(date) FROM daily_tasks)
""")

SQL_USD_CENTS = q("""
    UPDATE daily_tasks
    SET usd_cents = CAST(ROUND(COALESCE(display_value_usd, 0) * 100) AS INTEGER),
        is_active = 1
    WHERE date = (SELECT MAX(date) FROM daily_tasks)
""")

SQL_SUM = q("""
    SELECT COALESCE(SUM(usd_cents), 0)
    FROM daily_tasks
    WHERE date = (SELECT MAX(date) FROM daily_tasks) AND is_active = 1
""")

SQL_DEBUG_LAST10 = q("""
    SELECT date, code, display_value_usd, usd_cents, is_active
    FROM daily_tasks
    ORDER BY id DESC
    LIMIT 10
""")

async def main():
    async with Ctx() as db:
      # Debug: which date are we touching?
      d = await db.execute(SQL_TARGET_DATE)
      target = d.scalar()
      print(f"🎯 target date = {target}")

      print("🌙 Randomizing display_value_usd on target date ...")
      await db.execute(SQL_BACKFILL_RANDOM)
      await db.execute(SQL_USD_CENTS)

      val = await db.execute(SQL_SUM)
      cents = val.scalar() or 0
      print(f"✅ [today] active usd_cents = {cents}  (≈ ${cents/100:.2f})")

      print("\n[last 10 daily_tasks]")
      rows = await db.execute(SQL_DEBUG_LAST10)
      for r in rows.fetchall():
          print(tuple(r))

asyncio.run(main())
