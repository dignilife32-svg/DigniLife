# src/daily/auto_generate.py
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Dict, Iterable
from sqlalchemy.orm import Session
from datetime import datetime
import random
import re

from src.db import models  # expects models.DailyTask

# ---------- Rules & Helpers ----------

@dataclass
class GenRule:
    suffix: str
    reward_mult: Decimal  # e.g. Decimal("1.10") = +10%
    extra_meta: Dict[str, str] | None = None

VAR_RULES: Dict[str, List[GenRule]] = {
    "voice": [
        GenRule(" (5 words)", Decimal("1.10")),
        GenRule(" (7 words, clear)", Decimal("1.20")),
        GenRule(" (fast mode)", Decimal("1.05")),
    ],
    "geo": [
        GenRule(" + photo", Decimal("1.15")),
        GenRule(" + caption", Decimal("1.20")),
    ],
    "device": [
        GenRule(" (HD)", Decimal("1.10")),
        GenRule(" (secure)", Decimal("1.08")),
    ],
    "social": [
        GenRule(" (long form 60w)", Decimal("1.25")),
        GenRule(" (with emoji)", Decimal("1.05")),
    ],
    "data": [
        GenRule(" (strict)", Decimal("1.10")),
        GenRule(" (fast)", Decimal("1.05")),
    ],
    "sponsor": [
        GenRule(" (sponsored A)", Decimal("1.00")),
        GenRule(" (sponsored B)", Decimal("1.10")),
    ],
}

SAFE_CODE = re.compile(r"^[A-Z0-9]{2,6}$")

def _mk_variant_code(base_code: str, idx: int) -> str:
    base = base_code if SAFE_CODE.match(base_code) else "T"
    return f"{base}V{idx}"

def _exists_task(db: Session, code: str) -> bool:
    return db.query(models.DailyTask).filter_by(code=code).first() is not None

# ---------- Public API ----------

def generate_variants_for_task(db: Session, base_task: models.DailyTask, max_variants: int = 3) -> int:
    """Create up to N variants for one base task, idempotently."""
    rules = VAR_RULES.get(base_task.category, [])
    if not rules:
        return 0

    created = 0
    pick_rules = random.sample(rules, k=min(max_variants, len(rules)))
    for i, rule in enumerate(pick_rules, start=1):
        code = _mk_variant_code(base_task.code, i)
        if _exists_task(db, code):
            continue

        reward = Decimal(str(base_task.base_reward_usd)) * rule.reward_mult
        db.add(models.DailyTask(
            code=code,
            name=f"{base_task.name}{rule.suffix}",
            category=base_task.category,
            base_reward_usd=float(round(reward, 2)),
            created_at=datetime.utcnow(),
            is_variant=True,
            parent_code=base_task.code,
            meta=rule.extra_meta or {},
        ))
        created += 1

    if created:
        db.commit()
    return created


def bulk_generate_from_catalog(db: Session, categories: Iterable[str] | None = None, per_task_max: int = 2) -> int:
    """Scan catalog and generate variants across categories."""
    q = db.query(models.DailyTask)
    if categories:
        q = q.filter(models.DailyTask.category.in_(list(categories)))
    base_tasks = q.filter((models.DailyTask.is_variant == False) | (models.DailyTask.is_variant.is_(None))).all()

    total = 0
    for t in base_tasks:
        total += generate_variants_for_task(db, t, max_variants=per_task_max)
    return total

