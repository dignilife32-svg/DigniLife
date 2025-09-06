# src/router.py
from fastapi import FastAPI

# absolute imports (pylance warning လျော့စေ)
from src.daily.router import router as daily_router
from src.admin.router import router as admin_router
from src.wallet.router import router as wallet_router
from src.earn.router  import router as earn_router

def attach_routes(app: FastAPI) -> FastAPI:
    # user earning — daily task endpoints
    app.include_router(daily_router,  prefix="/earn/daily", tags=["daily"])

    # user earning — other (classic/summary etc.)
    app.include_router(earn_router,   prefix="/earn",       tags=["earn"])

    # wallet/balance/payout endpoints
    app.include_router(wallet_router, prefix="/wallet",     tags=["wallet"])

    # admin dashboards / reviews
    app.include_router(admin_router,  prefix="/admin",      tags=["admin"])
    return app

__all__ = ["attach_routes"]
