# src/app.py
from fastapi import FastAPI
  # absolute import
from src.admin.router import router as admin_router

def make_app() -> FastAPI:
    app = FastAPI(title="Dignilife", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    (app)
    app.include_router(admin_router)
    return app

# ASGI app instance
app = make_app()
