# src/daily/service.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List


@dataclass
class Bundle:
    id: str
    user_id: str
    expire_at: datetime
    minutes: int
    items: List[dict] = field(default_factory=list)


class DailyService:
    def __init__(self):
        self._bundles: Dict[str, Bundle] = {}
        self._summary: Dict[str, Dict[str, float]] = {}  # key = (user_id, yyyy-mm)

    def start_bundle(self, user_id: str, minutes: int) -> Bundle:
        now = datetime.now(timezone.utc)
        b = Bundle(
            id=f"B-{int(now.timestamp())}-{user_id}",
            user_id=user_id,
            minutes=minutes,
            expire_at=now + timedelta(minutes=minutes),
        )
        self._bundles[b.id] = b
        return b

    def list_bundles(self, limit: int = 5) -> List[Bundle]:
        return list(
            sorted(self._bundles.values(), key=lambda x: x.expire_at, reverse=True)
        )[:limit]

    def submit(self, user_id: str, bundle_id: str, items: List[dict]) -> float:
        b = self._bundles.get(bundle_id)
        if not b or b.user_id != user_id:
            raise ValueError("invalid bundle")
        b.items.extend(items)

        # naive reward rule: $0.50 per item (placeholder—later hook real scoring)
        reward = 0.5 * len(items)
        ym = datetime.now(timezone.utc).strftime("%Y-%m")
        self._summary.setdefault(user_id, {})
        self._summary[user_id][ym] = self._summary[user_id].get(ym, 0.0) + reward
        return reward

    def summary(self, user_id: str):
        ym = datetime.now(timezone.utc).strftime("%Y-%m")
        total = self._summary.get(user_id, {}).get(ym, 0.0)
        days = int(datetime.now().day)
        return {
            "user_id": user_id,
            "month": ym,
            "total_tasks": int(total / 0.5),  # based on rule above
            "total_reward_usd": round(total, 2),
            "daily_average_usd": round(total / max(1, days), 2),
        }


svc = DailyService()
