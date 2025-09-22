# src/middleware/explainer.py
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
import time, json

# (optional) policy yaml ကိုရှိရင်ဖတ်, မရှိရင် None နဲ့ ဆက်လုပ်
try:
    import yaml  # type: ignore
except Exception:
    yaml = None  # yaml မရှိခဲ့လည်းသာမန်လုပ်ဆောင်နိုင်စေ

_POLICY: Dict[str, Any] | None = None
def _load_policy() -> Dict[str, Any] | None:
    p = Path("confidence_policy.yaml")
    if p.exists() and yaml:
        try:
            return yaml.safe_load(p.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None

_POLICY = _load_policy()

def _grade_confidence(conf: float) -> str:
    if conf >= 0.8: return "high"
    if conf >= 0.6: return "medium"
    return "low"

def build_explanation(
    request=None,
    reply: str = "",
    signals: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Return a compact, human-readable explanation block to include in responses.
    - request.state.ai_signals (if present) is used as signals
    - policy rules (if available) are echoed for transparency
    """
    sig = signals or {}
    if request is not None and not sig:
        sig = getattr(getattr(request, "state", object()), "ai_signals", {}) or {}

    conf = float(sig.get("confidence", 0.0) or 0.0)
    tox  = float(sig.get("toxicity", 0.0) or 0.0)
    urg  = float(sig.get("intent_urgency", 0.0) or 0.0)

    why: list[str] = []
    why.append(f"confidence is {conf:.2f} ({_grade_confidence(conf)})")
    if urg: why.append(f"intent_urgency≈{urg:.2f}")
    if tox: why.append(f"toxicity≈{tox:.2f}")

    # policy hint (if YAML loaded)
    policy_hint: Dict[str, Any] | None = None
    if _POLICY:
        policy_hint = {
            "min_confidence": _POLICY.get("min_confidence"),
            "max_toxicity": _POLICY.get("max_toxicity"),
            "action_if_below": _POLICY.get("action_if_below", "warn"),
        }

    return {
        "ts": time.time(),
        "why": "; ".join(why) if why else "no signals",
        "signals": sig,
        "policy": policy_hint,
        "reply_preview": (reply[:120] + "…") if reply else ""
    }
