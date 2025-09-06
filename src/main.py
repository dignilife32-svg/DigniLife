# src/main.py
from fastapi import FastAPI
from src.router import attach_routes

app = FastAPI(title="DigniLife API")

# register all routes in one place
attach_routes(app)

@app.get("/health")
def health():
    return {"ok": True}
