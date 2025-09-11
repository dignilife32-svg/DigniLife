# src/admin/ui.py
from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/admin/ui", tags=["admin"])

@router.get("/ping")
async def ping():
    return {"ok": True}

@router.get("/login", response_class=HTMLResponse)
async def login_form():
    return """<form method="post" action="/admin/ui/login">
        <input name="username" placeholder="admin">
        <input name="password" type="password" placeholder="••••••">
        <button type="submit">Login</button>
    </form>"""

@router.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "admin":
        return {"message": "logged in (stub)"}
    raise HTTPException(status_code=401, detail="invalid credentials")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return "<h1>Admin Dashboard (stub)</h1>"
