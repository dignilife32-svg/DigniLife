#src/daily/task_catalog.py
from __future__ import annotations
from datetime import date

# Generator MUST return a list[dict] with keys that auto_injector understands:
# code, category, usd_cents, minutes, and either desc/title/prompt, actions(optional)

DEFAULT_SET = [
    {
        "code": "micro_reflect",
        "category": "micro",
        "usd_cents": 5,
        "minutes": 1,
        "desc": "Write a one-line daily goal.",
        "actions": ["text"],
    },
    {
        "code": "geo_ping",
        "category": "geo",
        "usd_cents": 25,
        "minutes": 2,
        "desc": "Confirm your approximate location.",
        "actions": ["button", "text"],
    },
    {
        "code": "visual_pick",
        "category": "visual",
        "usd_cents": 15,
        "minutes": 1,
        "desc": "Choose the correct image.",
        "actions": ["choice"],
    },
    {
        "code": "rate_short",
        "category": "feedback",
        "usd_cents": 20,
        "minutes": 1,
        "desc": "Rate a short text (1–5).",
        "actions": ["rating"],
    },
]

def generate_daily_tasks(for_date: date) -> list[dict]:
    # Later you can make this dynamic (locale, user segment, etc.)
    # For now, return a small but valid set.
    return DEFAULT_SET
