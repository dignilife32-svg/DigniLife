import json
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[2]  # project root
CFG_DIR = ROOT / "config"

_DEFAULT_RATES: Dict[str, Dict[str, float]] = {
    "prompt_rank": {"sec": 15, "usd": 1.00},
    "safety_tag": {"sec": 12, "usd": 0.75},
    "read_aloud": {"sec": 20, "usd": 1.00},
    "qr_proof": {"sec": 35, "usd": 1.75},
    "micro_lesson": {"sec": 70, "usd": 4.00},
    "geo_ping": {"sec": 18, "usd": 1.00},
}

_DEFAULT_TARGETS = {
    "default_bundle_minutes": 60,
    "min_bundle_minutes": 10,
    "max_bundle_minutes": 120,
    "target_usd_per_hour_low": 200,
    "target_usd_per_hour_high": 300,
}


def load_json(p: Path, default: dict) -> dict:
    try:
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def get_rates() -> Dict[str, Dict[str, float]]:
    return load_json(CFG_DIR / "daily_rates.json", _DEFAULT_RATES)


def get_targets() -> dict:
    return load_json(CFG_DIR / "daily_targets.json", _DEFAULT_TARGETS)
