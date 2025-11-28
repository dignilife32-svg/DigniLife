# src/routers/admin_ui.py
from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from jinja2 import Template
from fastapi.responses import HTMLResponse
from fastapi import Request, APIRouter

router = APIRouter(prefix="/admin", tags=["admin-ui"])
TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/ui", response_class=HTMLResponse)
async def admin_ui(request: Request):
    return templates.TemplateResponse("admin/dashboard.html", {"request": request})

@router.get("/ui/bonus")
async def bonus_ui(request: Request):
    return templates.TemplateResponse("admin/bonus_ui.html", {"request": request})

@router.get("/demo/ai", response_class=HTMLResponse)
async def admin_ai_demo(request: Request):
    html = (TEMPLATES_DIR / "admin/ai_reply.html").read_text()
    return HTMLResponse(html)
