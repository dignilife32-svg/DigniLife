# src/routers/safety_ui.py
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pathlib import Path


router = APIRouter(tags=["ui"])

# ---- paths (single source of truth) ----
TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
FACE_TPL      = TEMPLATES_DIR / "face_verify.html"
WITHDRAW_TPL  = TEMPLATES_DIR / "withdraw_demo.html"

@router.get("/ui/face-verify", response_class=HTMLResponse)
async def face_verify_page():
    return HTMLResponse(FACE_TPL.read_text(encoding="utf-8"))

@router.get("/ui/withdraw-demo", response_class=HTMLResponse)
async def withdraw_demo_page():
    return HTMLResponse(WITHDRAW_TPL.read_text(encoding="utf-8"))

@router.get("/ui/assist", response_class=HTMLResponse)
async def assist_page():
    return HTMLResponse((TEMPLATES_DIR/"assist_submit.html").read_text(encoding="utf-8"))

@router.get("/ui/voice", response_class=HTMLResponse)
async def voice_page():
    return HTMLResponse((TEMPLATES_DIR/"voice_assist.html").read_text(encoding="utf-8"))
