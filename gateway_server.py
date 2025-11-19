# gateway_server.py
# ---------------------------------------------------------------------
# Local-only payout gateway mock (admin-only). No external APIs.
# It receives a payout job and logs it as "ok" (or "error") for evidence.
# ---------------------------------------------------------------------

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone

import os
import json

app = FastAPI(title="DigniLife Payout Gateway (Local)")

# --- Config (env) ----------------------------------------------------
GATEWAY_TOKEN = os.getenv("PAYOUT_GATEWAY_TOKEN", "super-secret-123")

LOG_DIR = Path("runtime/ops")
LOG_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = LOG_DIR / "provider_payout_log.csv"
JSON_DIR = LOG_DIR / "provider_raw"
JSON_DIR.mkdir(parents=True, exist_ok=True)

if not CSV_PATH.exists():
    CSV_PATH.write_text(
        "ts_utc,withdrawal_id,amount_usd,method,dest,note,source,status,provider_ref\n",
        encoding="utf-8",
    )

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def csv_append(row: list[str]) -> None:
    CSV_PATH.write_text(CSV_PATH.read_text(encoding="utf-8") + ",".join(row) + "\n", encoding="utf-8")


# --- Schema -----------------------------------------------------------
class PayoutRequest(BaseModel):
    withdrawal_id: str = Field(..., min_length=6)
    amount_usd: float = Field(..., gt=0)
    method: str = Field(..., min_length=2)   # e.g. "tng" | "bank" | "paypal" | "prepaid"
    dest: str = Field(..., min_length=3)     # e.g. phone / account / iban / card
    note: Optional[str] = None
    source: Optional[str] = "worker_admin"


# --- Endpoint ---------------------------------------------------------
@app.post("/payout")
def payout(req: PayoutRequest, x_gateway_token: str = Header(default="")):
    if x_gateway_token != GATEWAY_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid gateway token")

    # Simple validations
    if not req.dest.strip():
        raise HTTPException(status_code=400, detail="Destination is required")

    ts = now_iso()

    # (Real impl would drive bank UI/API automation here.)
    # For now, log as success with a deterministic "provider_ref".
    provider_ref = f"OK:{req.method}:{req.dest[-4:]}:{req.withdrawal_id[:8]}"

    # Save JSON evidence
    raw_path = JSON_DIR / f"{req.withdrawal_id}.json"
    raw = {
        "ts_utc": ts,
        "request": req.dict(),
        "status": "ok",
        "provider_ref": provider_ref,
    }
    with raw_path.open("w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)

    # Append CSV
    csv_append(
        [
            ts,
            req.withdrawal_id,
            f"{req.amount_usd:.2f}",
            req.method,
            req.dest.replace(",", " "),
            (req.note or "").replace(",", " "),
            (req.source or "").replace(",", " "),
            "ok",
            provider_ref,
        ]
    )

    return {
        "ok": True,
        "status": "ok",
        "provider_ref": provider_ref,
        "ts_utc": ts,
    }
