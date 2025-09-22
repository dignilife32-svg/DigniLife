# src/utils/feedback_store.py
from __future__ import annotations
import json, os, threading, time
from typing import Any, Dict

class JSONFeedbackStore:
    def __init__(self, path: str = "data/feedback_data.jsonl"):
        self.path = path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as f:
                pass  # create empty file

    def append(self, item: Dict[str, Any]) -> None:
        item = dict(item)
        item.setdefault("ts", int(time.time()))
        with self._lock, open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

store = JSONFeedbackStore()
