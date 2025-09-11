# src/main.py

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# --- our project imports (keep these paths the same as your project) ---
from src.db.session import Base, engine                   # your SQLAlchemy Base (tables metadata)
                       # created in src/db/session.py and re-exported in __init__.py

from src.routers.rewards import router as rewards_router  # Rewards / Referrals API
from src.admin.ui import router as admin_ui_router        # simple admin UI routes (login, dashboard, etc.)
from src.admin.seed import seed_admin                     # optional admin seeder


def create_app() -> FastAPI:
    app = FastAPI(title="dignilife API")

    # ---- Mount /static if the folder exists (safe in dev/prod) ----
    static_dir = Path(__file__).resolve().parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # ---- Routers ----
    app.include_router(rewards_router)
    app.include_router(admin_ui_router, prefix="/admin/ui", tags=["admin"])

    # ---- Health check ----
    @app.get("/health", tags=["health"])
    async def health():
        return {"status": "ok"}

    # ---- Startup bootstrap (dev helper) ----
    @app.on_event("startup")
    async def bootstrap() -> None:
        """
        Local-dev safety: create tables if Alembic hasn't run yet.
        In real prod, rely on Alembic migrations exclusively.
        """
        try:
            Base.metadata.create_all(bind=engine)
        except Exception as exc:
            # Don't crash the app because of bootstrap; logs are enough.
            # Alembic migration flow will still work.
            print(f"[bootstrap] create_all skipped: {exc}")

        # Optional: ensure an initial admin user exists
        try:
            seed_admin()
        except Exception:
            # seeding is optional; ignore if it already exists
            pass

    return app


# ASGI entrypoint for `uvicorn src.main:app --reload`
app = create_app()
