# src/security.py
from typing import Optional
from fastapi import Header, Query, HTTPException, status

"""
Very small auth shim for dev/MVP.
- User ID:   pass as header `X-User-Id: <uuid>`  (or query ?user_id=)
- Admin:     header `X-Admin: true`
"""

async def CurrentUser(
    x_user_id: Optional[str] = Header(default=None, convert_underscores=False),
    user_id: Optional[str] = Query(default=None),
) -> str:
    uid = x_user_id or user_id
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing user identity (X-User-Id header or ?user_id=)",
        )
    return uid

async def require_user(
    x_user_id: Optional[str] = Header(default=None, convert_underscores=False),
) -> str:
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-User-Id header",
        )
    return x_user_id

async def require_admin(
    x_admin: Optional[str] = Header(default=None, convert_underscores=False),
) -> None:
    if not x_admin or str(x_admin).lower() not in ("1", "true", "yes"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin header required",
        )
