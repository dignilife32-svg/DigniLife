# src/admin/admin_ui_router.py
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates

# templates folder => templates/admin/*.html
TEMPLATES = Jinja2Templates(directory="templates/admin")

router = APIRouter(prefix="/admin/ui", tags=["admin-ui"])


@router.get("/ping")
async def ping():
    return {"ok": True, "at": "/admin/ui/ping"}


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return TEMPLATES.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    # demo credential (လိုသလိုပြင်)
    if email == "admin@digni.life" and password == "admin123":
        # 302 redirect to dashboard
        return RedirectResponse(url="/admin/ui/dashboard", status_code=302)

    # invalid => show form again with error
    return TEMPLATES.TemplateResponse(
        "login.html",
        {"request": request, "error": "Invalid credentials"},
        status_code=401,
    )


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return TEMPLATES.TemplateResponse("dashboard.html", {"request": request})
