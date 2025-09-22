# src/ai/auto_check.py
from typing import Tuple

def quality_check(payload: dict) -> Tuple[bool, str, float]:
    """
    Very simple heuristic:
    - payload ထဲက text/proof အရှည် စ etc. ကိုသုံးပြီး pass/fail စီးရဲ။
    """
    if not payload:
        return False, "empty payload", 0.1
    # demo logic
    return True, "ok", 0.9
