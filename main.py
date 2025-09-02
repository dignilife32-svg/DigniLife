# main.py  (project root)
from fastapi import FastAPI
from src.router import attach_routes

def make_app() -> FastAPI:
    app = FastAPI(title="Dignilife", version="0.1.0")

    @app.get("/")
    def root() -> dict[str, str]:
        return {"service": "dignilife", "status": "ok"}

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    attach_routes(app)
    return app

app = make_app()
