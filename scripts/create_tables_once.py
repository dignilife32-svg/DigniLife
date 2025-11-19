# scripts/create_tables_once.py
from src.db.session import engine
from src.db.models import Base as DBBase   # if your DailyTask Base is here
from src.wallet.models import Base as WalletBase
from sqlalchemy import text

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(DBBase.metadata.create_all)
        await conn.run_sync(WalletBase.metadata.create_all)

import asyncio; asyncio.run(main())
