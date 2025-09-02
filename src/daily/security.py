# Lightweight dev-time stubs; production မှာ device attestation/liveness addon ချိတ်မယ်
from typing import Dict, Any


def verify_session(headers: Dict[str, str]) -> str:
    """
    Return a user_id from headers. Dev default = 'demo'.
    In prod: validate JWT / device fingerprint / liveness flags.
    """
    return headers.get("x-user-id") or headers.get("X-User-Id") or "demo"


def basic_sanity_check(payload: Dict[str, Any]) -> bool:
    # ပြဿနာကြီးမရှိကြောင်းသာစစ် (bundle_id, structure, sizes)
    return bool(payload.get("bundle_id"))
