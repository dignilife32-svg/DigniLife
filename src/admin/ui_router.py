# src/admin/ui_router.py
from pathlib import Path
from fastapi import APIRouter, Request, Depends, Form, Response, HTTPException
from fastapi.templating import Jinja2Templates
from src.auth.security import make_token, ADMIN_KEY, COOKIE_NAME, require_user_cookie, verify_token
from src.auth.security import require_admin  # reuse for API fetches via cookie dep
from src.earn.service import get_task_stats
from src.wallet.service import get_all_wallets_summary, admin_list_withdrawals
from src.safety.service import get_reports_stats, get_sos_stats
import json

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(prefix="/admin/ui", tags=["admin-ui"])

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login_submit(request: Request, response: Response,
                 user_id: str = Form(...), admin_key: str = Form(...)):
    if admin_key != ADMIN_KEY:
        return templates.TemplateResponse("login.html",
                    {"request": request, "error": "Invalid admin key"}, status_code=401)
    token = make_token(user_id, "admin")
    # set cookie (HttpOnly for basic safety)
    response.set_cookie(COOKIE_NAME, token, httponly=True, samesite="lax", max_age=60*60*24)
    return templates.TemplateResponse("redirect.html",
                                      {"request": request, "to": "/admin/ui/dashboard"})

def _require_admin_cookie(request: Request):
    payload = require_user_cookie(request)  # verify + 401 if missing
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return payload

@router.get("/logout")
def logout(request: Request, response: Response):
    response.delete_cookie(COOKIE_NAME)
    return templates.TemplateResponse("login.html", {"request": request, "info": "Logged out"})

@router.get("/dashboard")
def dashboard(request: Request, admin=Depends(_require_admin_cookie)):
    # gather cards
    wallet = get_all_wallets_summary()
    tasks = get_task_stats()
    reports = get_reports_stats()
    sos = get_sos_stats()
    pending = admin_list_withdrawals(status="requested", limit=20)

    ctx = {
        "request": request,
        "admin_id": admin["sub"],
        "wallet": wallet,
        "tasks": tasks,
        "reports": reports,
        "sos": sos,
        "pending": pending["items"],
    }
    return templates.TemplateResponse("dashboard.html", ctx)
