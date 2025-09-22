# -*- coding: utf-8 -*-
from __future__ import annotations

def clamp(x, lo, hi): return max(lo, min(hi, x))

def compute_multiplier(*, streak_bonus: float, quality_bonus: float, penalty: float) -> float:
    return clamp(1.0 + streak_bonus + quality_bonus - penalty, 0.0, 2.0)

def compute_reward_usd(*, base: float, streak_bonus: float, quality_bonus: float, penalty: float):
    m = compute_multiplier(streak_bonus=streak_bonus, quality_bonus=quality_bonus, penalty=penalty)
    return round(base * m, 2), m
