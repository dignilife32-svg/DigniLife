# src/admin/ui.py
"""
Legacy simple Admin UI stub.

Main production admin UI is now served from `src/admin/ui_router.py`
with Jinja templates. This module is kept only for reference / manual
mounting and is NOT auto-mounted by the router scanner because it
does not expose a `router` attribute.
"""

from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import HTMLResponse

# NOTE: name = router_stub (NOT "router") so src.main auto scanner skips it.
router_stub = APIRouter(prefix="/admin/ui-legacy", tags=["admin-legacy"])


@router_stub.get("/ping")
async def ping():
    return {"ok": True, "legacy": True}


@router_stub.get("/login", response_class=HTMLResponse)
async def login_form():
    return """<form method="post" action="/admin/ui-legacy/login">
        <input name="username" placeholder="admin">
        <input name="password" type="password" placeholder="••••••">
        <button type="submit">Login</button>
    </form>"""


@router_stub.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "admin":
        return {"message": "logged in (stub)", "user": username}
    raise HTTPException(status_code=401, detail="invalid credentials")


@router_stub.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return "<h1>Admin Dashboard (legacy stub)</h1>"


__all__ = ["router_stub"]
