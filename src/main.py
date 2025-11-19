# src/main.py
from __future__ import annotations
import logging, importlib, pkgutil
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.wallet.router import router as wallet_router
from collections.abc import Iterator
from src.agi.router import  get_agi_router
from src.ai.diagnosis import init_runtime, report_startup_error
from src.ai.diagnosis import run_periodic_health_checks
from src.ai.diagnosis import record_runtime_error
from src.auth.router import router as auth_router
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

logger = logging.getLogger("dignilife")
logging.basicConfig(level=logging.INFO)

def create_app() -> FastAPI:
    init_runtime()  # runtime dirs + self_repair
    app = FastAPI()
    # ... routers, middleware, etc ...
    return app

try:
    app = create_app()
except Exception as exc:
    # AGI diagnostic helper ကို သုံးပြီး startup error ပြ
    report_startup_error(exc)
    # ပြီးရင် original error ကို ထပ်ပစ် (dev mode မှာ traceback လိုရအောင်)
    raise
EXPECTED_MIN_ROUTERS = 10  # အခု state ကိုသိပ္ပာင်ထား
def _assert_router_count(app: FastAPI) -> None:
    count = sum(1 for r in app.router.routes if getattr(r, "methods", None))
    if count < EXPECTED_MIN_ROUTERS:
        logger.warning("Routers low: %s < %s", count, EXPECTED_MIN_ROUTERS)

@app.on_event("startup")
async def on_startup() -> None:
    asyncio.create_task(run_periodic_health_checks(interval_sec=120))

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # AGI helper ကိုသုံးပြီး detailed info log ထုတ်
    record_runtime_error(
        exc,
        context={
            "path": str(request.url),
            "method": request.method,
        },
    )
    # client အတွက်တော့ simple messageပဲ
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 DigniLife starting up…")
    yield
    logger.info("🛑 DigniLife shutting down…")

app = FastAPI(title="DigniLife", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

@app.get("/health", tags=["health"])
async def health_ok():
    return {"ok": True}

def iter_router_modules(root_pkg: str = "src") -> Iterator[tuple[str, object]]:
    pkg = importlib.import_module(root_pkg)
    for finder, name, ispkg in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        if not (name.endswith(".router") or name.endswith(".routers")):
            continue
        try:
            mod = importlib.import_module(name)
        except Exception as e:
            record_runtime_error(e, {"phase": "import_router_module", "module": name})
            print(f"⚠️ Skipped router module import from {name}: {e}")
            continue
        if not hasattr(mod, "router"):
            continue
        yield name, mod

def _include_all_routers(app: FastAPI) -> None:
    count = 0
    for name, mod in iter_router_modules("src"):
        try:
            app.include_router(mod.router)
            logger.info(f"✅ Included router from {name}")
            count += 1
        except Exception as e:
            # 🔴 include_router မှာ တက်တဲ့ error တွေကိုလည်း AGI ဆီပို့
            record_runtime_error(e, {"phase": "include_router", "module": name})
            logger.warning(f"⚠️ Skipped router from {name}: {e}")
    if count == 0:
        logger.warning("⚠️ No routers discovered; make sure router.py exists and defines 'router'")
_include_all_routers(app)

app.include_router(auth_router)
# AGI router
agi_router = get_agi_router()
app.include_router(get_agi_router(), prefix="/_agi", tags=["AGI"])



