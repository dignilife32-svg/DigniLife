# src/main.py

import os
from fastapi import FastAPI
from fastapi import Response
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# our middleware & routers
from starlette.middleware.sessions import SessionMiddleware
from src.middleware.ai_guard import ai_guard_middleware
from src.middleware.explainer import build_explanation
from src.routers.ai_explain import router as ai_explain_router

from src.routers.admin_auth import router as admin_auth_router
from src.routers.admin_log import router as admin_log_router
from src.routers.admin import router as admin_router
from src.routers.tasks import router as tasks_router
from src.routers.ai_diagnostics import router as ai_diagnostics_router
from src.routers.ai_latency import router as ai_latency_router
from src.routers.ai_explain import router as ai_explain_router
from src.routers.admin_metrics import router as admin_metrics_router
from src.routers.admin_ui import router as admin_ui_router
from src.routers.admin_log_ui import router as admin_log_ui_router
from src.routers.feedback import router as feedback_router
from src.routers.earn import router as earn_router
from src.routers.wallet import router as wallet_router
from src.daily.router import router as daily_router
from src.classic.router import router as classic_router
from src.routers.echo import router as echo_router


def create_app() -> FastAPI:
    
    app = FastAPI(title="DigniLife API")


    #session for admin login
    SECRET = os.environ.get("SESSION_SECRET", "dev-secret-change-me")
    app.add_middleware(SessionMiddleware, secret_key=SECRET)

    app.mount("/static", StaticFiles(directory="static"), name="static")

    # AI Guard middleware – attaches signals; can fallback by policy
    app.middleware("http")(ai_guard_middleware)

    # --- routes defined INSIDE the factory (decorators need app in scope) ---
    @app.get("/health")
    async def health():
        return {"ok": True}

    
    @app.post("/echo")
    async def echo(request: Request):
        data = await request.json()
        signals = getattr(request.state, "ai_signals", {})
        return JSONResponse(
            content={
                "intent": "echo",
                "data": data,
                "signals": signals,
                "explain": build_explanation(),   # ✅ Step D2 attach
            }
        )
    
    # group routers (order doesn’t matter)
    
# ...
    app.include_router(daily_router)
    app.include_router(classic_router)
    app.include_router(echo_router, tags=["echo"])
    app.include_router(admin_auth_router)
    app.include_router(admin_router)
    app.include_router(admin_log_router)
    app.include_router(tasks_router, tags=["tasks"])
    app.include_router(ai_diagnostics_router)
    app.include_router(ai_latency_router)
    app.include_router(ai_explain_router)
    app.include_router(admin_metrics_router)
    app.include_router(admin_ui_router)
    app.include_router(admin_log_ui_router)
    app.include_router(ai_explain_router)
    app.include_router(feedback_router)
    app.include_router(earn_router)
    app.include_router(wallet_router)
    return app


# ASGI entrypoint
app = create_app()



@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)  # or serve a real icon la

# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"msg": "Hello DigniLife"}


# main.py (relevant part)
from fastapi import FastAPI
from src.classic.router import router as classic_router
from src.daily.router import router as daily_router
# ... အခြား router တွေ

def create_app() -> FastAPI:
    app = FastAPI(title="DigniLife API")

    # ... middleware, static, etc.

    app.include_router(daily_router)
    app.include_router(classic_router)   # <- ဒီတစ်ကြောင်းရှိရုံပဲ

    # DEBUG: registered routes ကို log ထုတ်စေ
    @app.on_event("startup")
    async def _dump_routes():
        print("=== ROUTES ===")
        for r in app.routes:
            print(getattr(r, "methods", None), r.path)

    return app

app = create_app()

