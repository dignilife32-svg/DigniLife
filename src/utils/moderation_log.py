import json, os, time
from typing import Dict, Any

LOG_DIR = os.environ.get("DG_LOG_DIR", "./runtime/logs")
LOG_PATH = os.path.join(LOG_DIR, "moderation.jsonl")

os.makedirs(LOG_DIR, exist_ok=True)

def log_event(payload: Dict[str, Any]) -> None:
    payload = dict(payload)
    payload["ts"] = time.time()
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
