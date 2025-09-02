# src/router.py
from fastapi import FastAPI
from .daily.router import router as daily_router

def attach_routes(app: FastAPI) -> FastAPI:
    app.include_router(daily_router)
    return app
