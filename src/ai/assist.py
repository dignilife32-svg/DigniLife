# src/ai/assist.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone
import time, os, base64, json
from collections import defaultdict, deque

# ------- Rate limit (per user/device) -------
ASSIST_RATE_PER_MIN = int(os.getenv("ASSIST_RATE_PER_MIN", "8"))
_ASSIST_RL_USER: Dict[str, deque] = defaultdict(deque)
_ASSIST_RL_DEV: Dict[str, deque] = defaultdict(deque)

def _enforce_assist_rl(user_id: str, device_id: str) -> None:
    now = time.time(); window = 60.0
    dq_u = _ASSIST_RL_USER[user_id]
    while dq_u and now - dq_u[0] > window: dq_u.popleft()
    if len(dq_u) >= ASSIST_RATE_PER_MIN: raise RuntimeError("RATE_LIMIT_USER")
    dq_u.append(now)
    dq_d = _ASSIST_RL_DEV[device_id]
    while dq_d and now - dq_d[0] > window: dq_d.popleft()
    if len(dq_d) >= ASSIST_RATE_PER_MIN: raise RuntimeError("RATE_LIMIT_DEVICE")
    dq_d.append(now)

# ------- Types -------
@dataclass
class AssistInput:
    user_id: str
    device_id: str
    text: Optional[str] = None
    image_b64: Optional[str] = None
    audio_b64: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    locale: Optional[str] = None
    task_hint: Optional[str] = None

@dataclass
class AssistPlan:
    task: str
    meta: Dict[str, Any]
    reason: str

@dataclass
class AssistResult:
    ok: bool
    task: str
    confidence: float
    payout_usd: float
    needs_review: bool
    reason: str
    meta: Dict[str, Any]
    ts_iso: str

# ------- Config / pricing -------
TASK_PRICES = {
    "scan_qr": float(os.getenv("ASSIST_PRICE_QR", "2.0")),
    "geo_ping": float(os.getenv("ASSIST_PRICE_GEO", "2.5")),
    "voice_3words": float(os.getenv("ASSIST_PRICE_VOICE3", "3.0")),
    "image_label": float(os.getenv("ASSIST_PRICE_IMG", "2.0")),
    "text_tag": float(os.getenv("ASSIST_PRICE_TEXT", "1.5")),
}
AUTO_CREDIT_TH = float(os.getenv("ASSIST_AUTOCREDIT_TH", "0.90"))

# ------- Wallet credit (soft dependency) -------
def _try_credit_wallet(user_id: str, usd: float, reason: str, meta: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Try to call your existing wallet credit function.
    Expected signature example:
        from src.services.wallet_tx import credit_earn
        tx = await credit_earn(user_id=user_id, amount=usd, currency="USD", reason=reason, meta=meta)
    We keep it sync wrapper; router will await an async shim.
    """
    try:
        from src.services.wallet_tx import credit_earn  # type: ignore
    except Exception:
        return False, None
    try:
        # NOTE: If your credit_earn is async, router will await it via run_in_threadpool or direct await.
        tx = credit_earn(user_id=user_id, amount=usd, currency="USD", reason=reason, meta=meta)  # type: ignore
        tx_id = getattr(tx, "id", None)
        return True, str(tx_id) if tx_id is not None else None
    except Exception:
        return False, None

# ------- Helpers -------
def _b64_ok(s: Optional[str]) -> bool:
    if not s: return False
    try:
        base64.b64decode(s, validate=True)
        return True
    except Exception:
        return False

def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()

# ------- Detection -------
KEYMAP = {
    "qr": "scan_qr",
    "code": "scan_qr",
    "location": "geo_ping",
    "geo": "geo_ping",
    "voice": "voice_3words",
    "speak": "voice_3words",
    "label": "image_label",
    "tag": "text_tag",
}

def detect_task(inp: AssistInput) -> AssistPlan:
    # 1) explicit hint wins
    if inp.task_hint in TASK_PRICES:  # e.g., "scan_qr"
        return AssistPlan(task=inp.task_hint, meta={}, reason="hint")

    # 2) heuristic from content
    t = (inp.text or "").lower()
    for k, v in KEYMAP.items():
        if k in t:
            return AssistPlan(task=v, meta={}, reason=f"keyword:{k}")
    # 3) evidence based
    if inp.image_b64: return AssistPlan(task="image_label", meta={}, reason="has_image")
    if inp.audio_b64: return AssistPlan(task="voice_3words", meta={}, reason="has_audio")
    if inp.lat is not None and inp.lon is not None:
        return AssistPlan(task="geo_ping", meta={}, reason="has_geo")
    # 4) default
    return AssistPlan(task="text_tag", meta={}, reason="default")

# ------- Auto-complete (mock/heuristic but deterministic) -------
def auto_complete(plan: AssistPlan, inp: AssistInput) -> AssistResult:
    # confidence scoring (simple but monotonic)
    conf = 0.5
    evid = []
    if inp.text: conf += 0.1; evid.append("text")
    if _b64_ok(inp.image_b64): conf += 0.2; evid.append("image")
    if _b64_ok(inp.audio_b64): conf += 0.15; evid.append("audio")
    if inp.lat is not None and inp.lon is not None: conf += 0.15; evid.append("geo")
    conf = max(0.0, min(0.99, conf))

    payout = TASK_PRICES.get(plan.task, 1.0)
    needs_review = conf < AUTO_CREDIT_TH

    reason = f"task={plan.task}; evidence={','.join(evid) or 'none'}; detect={plan.reason}"
    meta: Dict[str, Any] = {
        "detect_reason": plan.reason,
        "evidence": evid,
        "locale": inp.locale,
    }
    return AssistResult(
        ok=True, task=plan.task, confidence=conf, payout_usd=payout,
        needs_review=needs_review, reason=reason, meta=meta, ts_iso=_utc()
    )

# ------- Public entrypoint -------
def assist_once(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic, side-effect-safe. Router applies rate-limit & (optional) wallet credit.
    """
    try:
        _enforce_assist_rl(payload["user_id"], payload["device_id"])
    except RuntimeError as e:
        return {"ok": False, "reason": str(e), "ts_iso": _utc()}

    inp = AssistInput(
        user_id=payload["user_id"], device_id=payload["device_id"],
        text=payload.get("text"), image_b64=payload.get("image_b64"),
        audio_b64=payload.get("audio_b64"), lat=payload.get("lat"),
        lon=payload.get("lon"), locale=payload.get("locale"),
        task_hint=payload.get("task_hint")
    )

    plan = detect_task(inp)
    res = auto_complete(plan, inp)

    out = asdict(res)
    out["ok"] = True
    return out
