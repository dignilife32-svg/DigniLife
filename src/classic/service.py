# src/classic/service.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional
from sqlalchemy.orm import Session


# (example) API အသုံးပြုမယ့် dataclass/type တွေ – လိုရာထပ်ဖြည့်ပါ
@dataclass
class TaskDef:
    id: str
    level: str
    title: str
    prompt: str
    tips: List[str]
    reward: float  # USD / points – သင့်စနစ်အလိုက်ပြောင်း


def list_levels(db: Session) -> List[str]:
    """Classic mode အတွက် level list – ယာယီ hardcode. မကြာခင် DB query ပြောင်းမယ်."""
    # e.g. db.query(LevelModel).order_by(LevelModel.order).all()
    return ["beginner", "intermediate", "advanced", "jailbreak"]


def start_level(db: Session, *, user_id: str, level: str, minutes: int) -> Dict[str, object]:
    """
    User တစ်ယောက် classic level တစ်ခုစတင်တဲ့ action.
    အခုတော့ skeleton – နောက်တစ်လှည့်မှာ
    - idempotency (per day per level)
    - timezone handling
    - daily cap / earning rule
    - audit log
    စတာတွေ DB ခေါ်ပြီးဖြည့်မယ်။
    """
    # example skeleton:
    if level not in {"beginner", "intermediate", "advanced", "jailbreak"}:
        return {"ok": False, "reason": "invalid_level"}

    # TODO: write rows via ORM (e.g. EarnSession model) then commit
    # db.add(EarnSession(...)); db.commit()

    return {"ok": True, "level": level, "minutes": minutes, "user_id": user_id}
