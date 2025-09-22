# src/ai/self_update_engine.py
from __future__ import annotations
import json
from pathlib import Path
from statistics import mean
from loguru import logger

FEEDBACK_DIR = Path("data/feedback")
SUG_DIR = Path("runtime/suggestions")
SUG_DIR.mkdir(parents=True, exist_ok=True)

def load_feedback():
    scores = []
    if not FEEDBACK_DIR.exists():
        return scores
    for f in FEEDBACK_DIR.glob("*.jsonl"):
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                obj = json.loads(line)
                if "confidence_ok" in obj:
                    scores.append(1.0 if obj["confidence_ok"] else 0.0)
            except Exception:
                continue
    return scores

def suggest_policy():
    data = load_feedback()
    if not data:
        return None
    avg = mean(data)
    # simple heuristic: if lots of “not ok”, raise thresholds a bit
    delta = -0.05 if avg > 0.8 else (0.05 if avg < 0.5 else 0.0)
    suggestion = {
        "suggested_delta": delta,
        "rationale": f"avg_feedback_ok={avg:.2f}",
        "apply_to": {"confidence.high": delta, "confidence.medium": delta},
    }
    out = SUG_DIR / "confidence_policy.generated.yaml"
    out.write_text(json.dumps(suggestion, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Policy suggestion written to {out}")
    return suggestion
