#src/routers/admin_auth.py
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os

router = APIRouter(prefix="/admin", tags=["admin-auth"])

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        "admin/login.html", {"request": request, "err": None}
    )


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    if email != ADMIN_USER or password != ADMIN_PASS:
        return templates.TemplateResponse(
            "admin/login.html",
            {"request": request, "err": "Invalid credentials"},
            status_code=401,
        )

    request.session["admin"] = True
    return RedirectResponse(url="/admin/ui", status_code=303)


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=303)
