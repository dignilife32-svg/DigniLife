"""
Seed Currencies - Initialize supported currencies
"""
import sys
import os
import asyncio
from datetime import datetime
from uuid import uuid4

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.session import AsyncSessionLocal
from src.db.models import Currency


CURRENCIES = [
    {"code": "USD", "name": "US Dollar", "symbol": "$"},
    {"code": "MMK", "name": "Myanmar Kyat", "symbol": "K"},
    {"code": "THB", "name": "Thai Baht", "symbol": "฿"},
    {"code": "PHP", "name": "Philippine Peso", "symbol": "₱"},
    {"code": "VND", "name": "Vietnamese Dong", "symbol": "₫"},
    {"code": "IDR", "name": "Indonesian Rupiah", "symbol": "Rp"},
    {"code": "MYR", "name": "Malaysian Ringgit", "symbol": "RM"},
    {"code": "SGD", "name": "Singapore Dollar", "symbol": "S$"},
    {"code": "INR", "name": "Indian Rupee", "symbol": "₹"},
    {"code": "BDT", "name": "Bangladeshi Taka", "symbol": "৳"},
]


async def seed_currencies():
    """Seed currencies into database"""
    async with AsyncSessionLocal() as session:
        try:
            from sqlalchemy import select
            result = await session.execute(select(Currency))
            existing = result.scalars().all()
            
            if len(existing) > 0:
                print(f"⚠️  Currencies already exist ({len(existing)} found). Skipping seed.")
                return
            
            for curr_data in CURRENCIES:
                currency = Currency(
                    id=uuid4(),
                    code=curr_data["code"],
                    name=curr_data["name"],
                    symbol=curr_data["symbol"],
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                session.add(currency)
            
            await session.commit()
            print(f"✅ Successfully seeded {len(CURRENCIES)} currencies!")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error seeding currencies: {e}")
            raise


if __name__ == "__main__":
    print("🌱 Seeding currencies...")
    asyncio.run(seed_currencies())