#src/routers/admin_guard.py
from fastapi import Request, HTTPException, status

def require_admin(request: Request):
    if not request.session.get("admin"):
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/admin/login"}
        )
    return True
