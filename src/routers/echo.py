# src/routers/echo.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/echo")
async def echo(request: Request):
    data = await request.json()
    signals = getattr(request.state, "ai_signals", {})  # MUST
    return JSONResponse({
        "intent": "echo",
        "data": data,
        "signals": signals,  # <- this line REQUIRED
    })
