#src/ai/security.py
from __future__ import annotations
import base64, uuid

def verify_face_b64(image_b64: str, user_id: str) -> bool:
    # stub: return True if image payload exists; replace with provider later
    try:
        if not image_b64: return False
        base64.b64decode(image_b64.encode("utf-8"))
        return True
    except Exception:
        return False

def score_withdrawal_risk(*, user_id: str, amount_usd_cents: int, device_fp: str|None) -> tuple[str,float]:
    """
    returns (reason, confidence) where confidence 0..1
    Rule of thumb:
      - amounts <= $100 always high confidence ok
      - new device or missing device -> low
    """
    if amount_usd_cents <= 100*100:
        return ("ok_small_amount", 0.98)
    if not device_fp:
        return ("missing_device_fp", 0.40)
    return ("ok_default", 0.80)
