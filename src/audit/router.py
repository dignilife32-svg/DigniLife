# src/audit/router.py
from __future__ import annotations
import os
from typing import Optional, List
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_session_ctx

router = APIRouter(prefix="/audit", tags=["audit"])

def _require_admin(x_admin_key: Optional[str] = Header(default=None)) -> None:
    want = os.getenv("ADMIN_KEY", "letmein")
    if not x_admin_key or x_admin_key != want:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="admin key required")

# --- table bootstrap (idempotent) ---
CREATE_SQL = """
CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ip TEXT,
  method TEXT,
  path TEXT,
  user_id TEXT,
  status INTEGER,
  ms INTEGER
);
"""
@router.on_event("startup")
async def _ensure_table() -> None:
    async with get_session_ctx() as db:
     await db.execute(text(CREATE_SQL))
     await db.commit()

# --- tiny helper used by main.py to record a row ---
async def write_audit_row(db: AsyncSession, ip: str, method: str, path: str, user_id: Optional[str], status: int, ms: int):
    await db.execute(text(
        "INSERT INTO audit_log (ip, method, path, user_id, status, ms) VALUES (:ip,:m,:p,:u,:s,:ms)"
    ), {"ip": ip, "m": method, "p": path, "u": user_id, "s": status, "ms": ms})

# --- admin views ---
@router.get("/logs", dependencies=[Depends(_require_admin)])
async def logs(limit: int = 100, db: AsyncSession = Depends(get_session_ctx)):
    rows = (await db.execute(text(
        "SELECT ts, ip, method, path, user_id, status, ms FROM audit_log ORDER BY id DESC LIMIT :l"
    ), {"l": limit})).all()
    return [{"ts": ts, "ip": ip, "method": m, "path": p, "user_id": u, "status": s, "ms": ms} for (ts, ip, m, p, u, s, ms) in rows]

@router.get("/ui", response_class=HTMLResponse, dependencies=[Depends(_require_admin)])
async def ui(limit: int = 200, db: AsyncSession = Depends(get_session_ctx)):
    rows = (await db.execute(text(
        "SELECT ts, ip, method, path, user_id, status, ms FROM audit_log ORDER BY id DESC LIMIT :l"
    ), {"l": limit})).all()
    trs = "".join(
        f"<tr><td>{ts}</td><td>{ip}</td><td>{m}</td><td>{p}</td><td>{u or ''}</td><td>{s}</td><td>{ms}</td></tr>"
        for (ts, ip, m, p, u, s, ms) in rows
    )
    return HTMLResponse(f"""
      <html><body style="font-family:system-ui;margin:24px">
        <h3>Audit logs</h3>
        <table border="1" cellspacing="0" cellpadding="6">
          <tr><th>ts</th><th>ip</th><th>method</th><th>path</th><th>user</th><th>status</th><th>ms</th></tr>
          {trs or '<tr><td colspan=7>(empty)</td></tr>'}
        </table>
      </body></html>
    """)
