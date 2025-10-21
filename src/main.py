# src/main.py
from __future__ import annotations

import os, asyncio
import importlib
from typing import Optional, Sequence
from contextlib import suppress
from fastapi import FastAPI, Request
from src.db.session import create_tables_once, AsyncSessionLocal

from src.routers import withdraw
from src.routers import assist as assist_router
from src.routers import voice as voice_router
from src.routers import admin_inject as admin_inject_router
from src.routers import safety_ui
from src.safety import facegate, proofguard
from src.ai_worker.service import router as ai_worker_router
from src.ai_worker.service import run_ai_worker_cycle
from src.routers.playground import router as playground_router
from src.routers import  ai_chat
from src.middleware.authsig import AuthSignatureMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.routing import APIRouter
from dotenv import load_dotenv

# ===== Core (required) routers: keep these imports exact =====
# Each module must expose: router = APIRouter(...)
from src.daily.router import router as daily_router
from src.bonus.router import router as bonus_router
from src.wallet import router as wallet_router
from src.sync import router as sync_router
from src.wallet.summary import router as wallet_summary_router
from src.middleware.ratelimit import RateLimitMiddleware
from src.middleware.ratelimit_radis import RedisRateLimitMiddleware

from src.middleware.idempotency import IdempotencyMiddleware

AI_WORKER_INTERVAL_SEC = int(os.getenv("AI_WORKER_INTERVAL_SEC", "600"))  # 10 minutes default


# ===== Optional middleware (safe import; ok if missing) =====
try:  # starlette session (optional)
    from starlette.middleware.sessions import SessionMiddleware  # type: ignore
except Exception:  # pragma: no cover
    SessionMiddleware = None  # type: ignore

try:  # project auth middleware (optional)
    from src.middleware.auth import AuthMiddleware  # type: ignore
except Exception:  # pragma: no cover
    AuthMiddleware = None  # type: ignore

load_dotenv(os.getenv("ENV_FILE", ".env"))
# ---------- helpers ----------
def try_import_router(dotted: str, attr: str = "router") -> Optional[APIRouter]:
    """
    Import APIRouter from dotted path safely.
    Returns None if module/attr not found or attr is not an APIRouter.
    """
    try:
        module = importlib.import_module(dotted)
        obj = getattr(module, attr, None)
        if isinstance(obj, APIRouter):
            return obj
    except Exception:
        pass
    return None


def safe_include(app: FastAPI, r: Optional[APIRouter], **kw) -> None:
    """
    Include router only when it is valid (not None and has routes).
    Avoids AttributeError like: module ... has no attribute 'routes'
    """
    if r and getattr(r, "routes", None):
        app.include_router(r, **kw)


# ---------- app factory ----------
def create_app() -> FastAPI:
    app = FastAPI(title="DigniLife API", version="0.1.0")

    # Static files (optional; useful for admin UI assets)
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    static_dir = os.path.abspath(static_dir)
    if os.path.isdir(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Session middleware (optional, enable if SECRET is set)
    secret = os.getenv("SESSION_SECRET")
    if SessionMiddleware and secret:
        app.add_middleware(SessionMiddleware, secret_key=secret)

    # Project auth middleware (optional)
    if AuthMiddleware:
        
        app.add_middleware(
            AuthSignatureMiddleware,
            redis_url=os.getenv("DL_REDIS_URL", "redis://localhost:6379/0"),
            replay_ttl_sec=60, clock_skew_sec=60)
            
                           
        app.add_middleware(AuthMiddleware)
        app.add_middleware(RateLimitMiddleware)
        app.add_middleware(
    IdempotencyMiddleware,
    redis_url="redis://localhost:6379",
    ttl=86400
)
        app.add_middleware(RedisRateLimitMiddleware,
    redis_url="redis://localhost:6379/0",
    prefix="dignilife:rate",
    user_limit=60,
    route_limit=120,
    window_seconds=60,
    fail_open=True,
    header_user_id="X-User-Id",
)

    # Health
    @app.get("/health")
    async def health() -> dict[str, bool]:
        return {"ok": True}

    # Simple echo (handy during bring-up)
    @app.post("/echo")
    async def echo(request: Request):
        data = await request.json()
        return JSONResponse(content={"t_intent": "echo", "data": data})

    # --- Core routers (order independent) ---
    app.include_router(daily_router)    # <- IMPORTANT: use .router (APIRouter object)
    app.include_router(bonus_router)
    app.include_router(wallet_router.router)
    app.include_router(withdraw.router)
    app.include_router(ai_worker_router)
    
    app.include_router(sync_router.router)
    app.include_router(wallet_summary_router)
    app.include_router(playground_router)
    app.include_router(ai_chat.router)
    app.include_router(safety_ui.router)
    app.include_router(facegate.router)
    app.include_router(assist_router.router)
    app.include_router(voice_router.router)
    app.include_router(admin_inject_router.router)
    

    # --- Optional routers (load only if available) ---
    # keep names short to avoid shadowing local names
    opt_paths: Sequence[str] = (
        # admin area
        "src.admin.router",
        "src.admin.admin_ui_router",
        "src.admin.admin_log_ui",
        "src.admin.admin_metrics",
        "src.admin.admin_auth",
        "src.admin.review",
        # ai / diagnostics
        "src.routers.ai_explain",
        "src.routers.ai_latency",
        "src.routers.ai_ops",
        "src.routers.ai_diagnostics",
        # general routers in src/routers
        "src.routers.echo",
        "src.routers.feedback",
        "src.routers.rewards",
        "src.routers.tasks",
        "src.routers.wallet",
        # realtime/ws (optional)
        "src.realtime.ws",
    )
    for dotted in opt_paths:
        safe_include(app, try_import_router(dotted))

    # Dev: dump routes on startup (optional; safe to remove later)
    @app.on_event("startup")
    async def _startup() -> None:
        # 1) DB schema (safe to call multiple times)
        await create_tables_once()

        # 2) Dev helper: print all routes (keep or remove later)
        try:
            for r in app.routes:
                path = getattr(r, "path", None) or getattr(r, "path_format", "")
                methods = getattr(r, "methods", None)
                m = ", ".join(sorted(methods)) if methods else ""
                print(f"[ROUTE] {path} {m}")
        except Exception:
            pass

        # 3) Background AI worker loop
        async def loop():
            # optional small delay to let server finish warming up
            await asyncio.sleep(1)
            while True:
                try:
                    async with AsyncSessionLocal() as db:
                        await run_ai_worker_cycle(db)
                except Exception as e:
                    # don't crash the app; just log and continue
                    print(f"[AI_WORKER] cycle error: {e!r}")
                await asyncio.sleep(AI_WORKER_INTERVAL_SEC)

        # keep a handle for graceful shutdown
        app.state.ai_worker_task = asyncio.create_task(loop())

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        # 4) stop the background loop cleanly
        task = getattr(app.state, "ai_worker_task", None)
        if task:
            task.cancel()
            with suppress(Exception):
                await task

    return app




# ASGI entrypoint for uvicorn
app = create_app()
