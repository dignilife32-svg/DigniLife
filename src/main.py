# src/main.py
from __future__ import annotations

import os
import asyncio
import importlib
import logging
import pkgutil
from collections.abc import Iterator
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.ai.diagnosis import (
    init_runtime,
    run_periodic_health_checks,
    record_runtime_error,
    report_startup_error,
)
from src.agi.router import get_agi_router

logger = logging.getLogger("dignilife")
logging.basicConfig(level=logging.INFO)


# -----------------------------
# Router auto-discovery
# -----------------------------
def iter_router_modules(root_pkg: str = "src.routers") -> Iterator[tuple[str, object]]:
    """
    Walk `src/routers` package and yield (module_name, module_obj)
    for any module that exposes a top-level `router` attribute.
    """
    try:
        pkg = importlib.import_module(root_pkg)
    except ImportError as e:
        logger.warning("Router package %s not found: %s", root_pkg, e)
        return iter([])

    def _iter() -> Iterator[tuple[str, object]]:
        for _, name, ispkg in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
            if ispkg:
                continue
            try:
                mod = importlib.import_module(name)
            except Exception as e:
                # import error -> send to AGI diagnostics
                record_runtime_error(e, {"phase": "import_router_module", "module": name})
                logger.warning("⚠️ Skipped router module import from %s: %s", name, e)
                continue
            if hasattr(mod, "router"):
                yield name, mod

    return _iter()


EXPECTED_MIN_ROUTERS = 10


def _include_all_routers(app: FastAPI) -> None:
    count = 0
    for name, mod in iter_router_modules("src.routers"):
        try:
            app.include_router(mod.router)  # type: ignore[attr-defined]
            logger.info("✅ Included router from %s", name)
            count += 1
        except Exception as e:
            record_runtime_error(e, {"phase": "include_router", "module": name})
            logger.warning("⚠️ Skipped router from %s: %s", name, e)

    if count == 0:
        logger.warning(
            "⚠️ No routers discovered under src.routers; "
            "make sure each router file defines a top-level `router`"
        )
    elif count < EXPECTED_MIN_ROUTERS:
        logger.warning("Routers low: %s < %s", count, EXPECTED_MIN_ROUTERS)


# -----------------------------
# Lifespan hooks
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 DigniLife starting up…")
    try:
        # runtime dirs + self-repair, etc.
        init_runtime()
    except Exception as exc:
        # startup diagnostics for AGI
        report_startup_error(exc)
        # re-raise so dev can see traceback in console
        raise

    # periodic health checks (background task)
    asyncio.create_task(run_periodic_health_checks(interval_sec=120))

    yield

    logger.info("🛑 DigniLife shutting down…")


# -----------------------------
# App factory
# -----------------------------
def create_app() -> FastAPI:
    app = FastAPI(title="DigniLife", lifespan=lifespan)

    # CORS (open – adjust later if needed)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
        )
    app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "dev-secret-change-me"),
)
    
    @app.get("/health", tags=["health"])
    async def health_ok():
        return {"ok": True}

    # Global exception handler – log via AGI diagnostics
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        record_runtime_error(
            exc,
            context={
                "path": str(request.url),
                "method": request.method,
            },
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # Include all feature routers under src/routers/*
    _include_all_routers(app)

    # AGI router (explicit; may live outside src/routers/)
    try:
        agi_router = get_agi_router()
        app.include_router(agi_router, prefix="/_agi", tags=["AGI"])
        logger.info("✅ Included AGI router at /_agi")
    except Exception as e:
        record_runtime_error(e, {"phase": "include_agi_router"})
        logger.warning("⚠️ Failed to include AGI router: %s", e)

    return app


# ASGI instance
try:
    app = create_app()
except Exception as exc:
    # last-resort safety; should normally be handled inside lifespan/init_runtime
    report_startup_error(exc)
    raise
