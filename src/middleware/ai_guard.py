from typing import Tuple, Literal, Dict, Any
from .profanity import scrub
from ..utils.moderation_log import log_event

Action = Literal["block", "soften", "allow"]

def guard_user_text(user_id: str, text: str) -> Tuple[Action, str, Dict[str, Any]]:
    """
    Basic policy:
    - if many profanity hits => soften (mask + prepend gentle reminder)
    - if extreme (very long with many hits) => block
    - else allow
    """
    clean, hits = scrub(text or "")
    length = len(text or "")
    meta = {"hits": hits, "length": length}

    if hits >= 6 or (hits >= 3 and length < 20):
        # looks like targeted harassment / pure abuse
        meta["reason"] = "heavy_profanity"
        return "block", "We can’t send this message. Please rephrase respectfully.", meta

    if hits >= 1:
        meta["reason"] = "light_profanity"
        softened = "Note: we masked some words for respect.\n" + clean
        return "soften", softened, meta

    meta["reason"] = "clean"
    return "allow", text, meta

def audit_guard(user_id: str, original: str, action: Action, final_text: str, meta: Dict[str, Any]) -> None:
    log_event({
        "kind": "guard",
        "user_id": user_id,
        "action": action,
        "original": original,
        "final": final_text,
        "meta": meta
    })
