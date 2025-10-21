# src/admin/admin_ui_router.py
from __future__ import annotations

import os
from typing import Optional
from fastapi import APIRouter, Depends, Header, Query, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session

ui = APIRouter(prefix="/admin/ui", tags=["admin-ui"])


def _require_admin(x_admin_key: Optional[str] = Header(default=None)) -> str:
    want = os.getenv("ADMIN_KEY", "letmein")
    if not x_admin_key or x_admin_key != want:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="admin key required")
    return x_admin_key


@ui.get("/", response_class=HTMLResponse)
async def home(_: str = Depends(_require_admin)):
    return HTMLResponse("""
    <html><body style="font-family:system-ui;margin:24px">
      <h2>Admin UI</h2>
      <ul>
        <li><a href="./tasks">Tasks</a></li>
        <li><a href="./ledger?user_id=demo_user">Ledger (demo_user)</a></li>
      </ul>
      <p style="color:#888">Send header <code>x-admin-key</code> with value you set in <code>ADMIN_KEY</code> (default <b>letmein</b>).</p>
    </body></html>
    """)


@ui.get("/tasks", response_class=HTMLResponse)
async def tasks_page(
    _: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_session),
):
    rows = (await db.execute(text("""
        SELECT code, category, display_value_usd, expected_time_sec, is_active
        FROM daily_tasks ORDER BY code ASC
    """))).all()
    trs = "".join(
        f"<tr><td>{c}</td><td>{cat}</td><td>${val:.2f}</td><td>{secs}s</td><td>{'✅' if bool(act) else '❌'}</td></tr>"
        for (c, cat, val, secs, act) in rows
    )
    html = f"""
    <html><body style="font-family:system-ui;margin:24px">
      <h3>Tasks</h3>
      <form method="post" action="./task/upsert" style="margin-bottom:16px">
        <input name="code" placeholder="code" required>
        <input name="category" placeholder="category" value="general">
        <input name="display_value_usd" type="number" step="0.01" value="1.00">
        <input name="expected_time_sec" type="number" value="60">
        <input name="user_prompt" placeholder="prompt" size="30">
        <input name="description" placeholder="description" size="30">
        <label>active <input name="is_active" type="checkbox" checked></label>
        <button type="submit">Upsert</button>
      </form>
      <table border="1" cellspacing="0" cellpadding="6">
        <tr><th>code</th><th>category</th><th>value</th><th>time</th><th>active</th></tr>
        {trs or '<tr><td colspan=5>(no rows)</td></tr>'}
      </table>
      <p><a href="../">⬅ back</a></p>
    </body></html>
    """
    return HTMLResponse(html)


@ui.post("/task/upsert", response_class=HTMLResponse)
async def upsert_task_form(
    _: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_session),
    code: str = Query(...),
    category: str = Query("general"),
    display_value_usd: float = Query(1.0),
    expected_time_sec: int = Query(60),
    user_prompt: str = Query(""),
    description: str = Query(""),
    is_active: Optional[str] = Query(None),
):
    await db.execute(text("""
        INSERT INTO daily_tasks (code, category, display_value_usd, expected_time_sec,
                                 user_prompt, description, is_active)
        VALUES (:code, :category, :val, :secs, :prompt, :desc, :active)
        ON CONFLICT(code) DO UPDATE SET
            category=excluded.category,
            display_value_usd=excluded.display_value_usd,
            expected_time_sec=excluded.expected_time_sec,
            user_prompt=excluded.user_prompt,
            description=excluded.description,
            is_active=excluded.is_active
    """), {
        "code": code, "category": category, "val": display_value_usd, "secs": expected_time_sec,
        "prompt": user_prompt, "desc": description, "active": 1 if is_active else 0
    })
    return HTMLResponse('<meta http-equiv="refresh" content="0; url=./tasks">')


@ui.get("/ledger", response_class=HTMLResponse)
async def ledger_page(
    _: str = Depends(_require_admin),
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_session),
):
    rows = (await db.execute(text("""
        SELECT id, amount_usd, ref, note, created_at
        FROM wallet_ledger
        WHERE user_id = :u
        ORDER BY id DESC LIMIT 100
    """), {"u": user_id})).all()
    trs = "".join(
        f"<tr><td>{i}</td><td>{amt:.2f}</td><td>{ref or ''}</td><td>{note or ''}</td><td>{ts}</td></tr>"
        for (i, amt, ref, note, ts) in rows
    )
    html = f"""
    <html><body style="font-family:system-ui;margin:24px">
      <h3>Ledger for <code>{user_id}</code></h3>
      <table border="1" cellspacing="0" cellpadding="6">
        <tr><th>id</th><th>amount_usd</th><th>ref</th><th>note</th><th>created_at</th></tr>
        {trs or '<tr><td colspan=5>(no rows)</td></tr>'}
      </table>
      <p><a href="../">⬅ back</a></p>
    </body></html>
    """
    return HTMLResponse(html)
