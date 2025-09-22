# src/classic/service.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Any, Optional
import uuid
import math

@dataclass
class TaskDef:
    id: str
    level: str          # beginner | intermediate | advanced | jailbreak
    title: str
    prompt: str
    tips: List[str]
    reward: float       # USD

@dataclass
class Bundle:
    id: str
    user_id: str
    level: str
    items: List[TaskDef] = field(default_factory=list)
    expire_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(minutes=30))

class ClassicService:
    """
    In-memory prototype service for Classic Earn.
    TODO(db): persist bundles, attempts, and earnings to DB.
    """
    def __init__(self) -> None:
        self._bundles: Dict[str, Bundle] = {}
        self._summary: Dict[str, Dict[str, float]] = {}      # user_id -> {"total": x, "count": n}
        self._catalog: Dict[str, List[TaskDef]] = self._build_catalog()

    # ---- Public API ----
    def levels(self) -> List[str]:
        return ["beginner", "intermediate", "advanced", "jailbreak"]

    def start_bundle(self, user_id: str, level: str = "beginner", minutes: int = 30) -> Bundle:
        level = level.lower()
        if level not in self._catalog:
            level = "beginner"
        items = self._sample_tasks(level, k=5)
        b = Bundle(
            id=f"c-{uuid.uuid4().hex[:8]}",
            user_id=user_id,
            level=level,
            items=items,
            expire_at=datetime.now(timezone.utc) + timedelta(minutes=minutes),
        )
        self._bundles[b.id] = b
        return b

    def next_task(self, user_id: str, level: Optional[str] = None) -> Dict[str, Any]:
        # Try to reuse the latest non-expired bundle of that level
        bundle = self._latest_bundle(user_id=user_id, level=level)
        if not bundle:
            bundle = self.start_bundle(user_id=user_id, level=level or "beginner", minutes=30)
        # Pop the next remaining task
        for t in list(bundle.items):
            bundle.items.remove(t)
            return self._task_to_dict(bundle, t)
        # If bundle empty, start a new one
        bundle = self.start_bundle(user_id=user_id, level=level or bundle.level, minutes=30)
        t = bundle.items.pop(0)
        return self._task_to_dict(bundle, t)

    def submit(self, user_id: str, bundle_id: str, task_id: str,
               output: str, meta: Dict[str, Any]) -> Tuple[bool, float, str]:
        b = self._bundles.get(bundle_id)
        if not b or b.user_id != user_id:
            return False, 0.0, "Invalid or expired bundle"
        # Very light-weight scoring (prototype). Replace with rubric/LLM judge later.
        base = self._task_by_id(b.level, task_id)
        if not base:
            return False, 0.0, "Unknown task"
        score = self._score(output, base)
        reward = round(base.reward * score, 2)
        # Update summary
        s = self._summary.setdefault(user_id, {"total": 0.0, "count": 0.0})
        s["total"] += reward
        s["count"] += 1
        return True, reward, f"Accepted (score={score:.2f})"

    def summary(self, user_id: str) -> Dict[str, Any]:
        s = self._summary.get(user_id, {"total": 0.0, "count": 0.0})
        days = max(1, (datetime.now(timezone.utc) - datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)).days + 1)
        avg = s["total"] / max(1, s["count"])
        return {
            "user_id": user_id,
            "total_tasks": int(s["count"]),
            "total_reward_usd": round(s["total"], 2),
            "classic_average_usd": round(avg, 2),
        }

    # ---- Internals ----
    def bundle_dict(self, b: Bundle) -> Dict[str, Any]:
        return {
            "id": b.id,
            "user_id": b.user_id,
            "level": b.level,
            "items": [self._task_public(td) for td in b.items],
            "expire_at": b.expire_at.isoformat(),
        }

    def _task_to_dict(self, b: Bundle, t: TaskDef) -> Dict[str, Any]:
        d = self._task_public(t)
        d["bundle_id"] = b.id
        return d

    def _task_public(self, t: TaskDef) -> Dict[str, Any]:
        return {
            "id": t.id,
            "level": t.level,
            "title": t.title,
            "prompt": t.prompt,
            "tips": t.tips,
            "reward": t.reward,
        }

    def _build_catalog(self) -> Dict[str, List[TaskDef]]:
        """
        Prototype task bank. Each task is intentionally concise.
        Real system will load from DB or YAML.
        """
        return {
            "beginner": [
                TaskDef("b1", "beginner", "Summarize text",
                        "Summarize this in 3 bullets: 'The solar system has eight planets...'",
                        ["Use short bullets", "No fluff"], 0.15),
                TaskDef("b2", "beginner", "Rewrite friendly",
                        "Rewrite this email more friendly: 'Send report now.'",
                        ["Keep it concise", "Polite tone"], 0.15),
                TaskDef("b3", "beginner", "Extract data",
                        "From this paragraph, extract 3 countries mentioned.",
                        ["Return a JSON array"], 0.15),
                TaskDef("b4", "beginner", "Classify sentiment",
                        "Label the sentiment (positive/neutral/negative): 'I kinda like it.'",
                        ["One word only"], 0.15),
                TaskDef("b5", "beginner", "Generate hashtags",
                        "Generate 5 hashtags for a healthy breakfast reel.",
                        ["No spaces", "lowercase"], 0.15),
            ],
            "intermediate": [
                TaskDef("i1", "intermediate", "Prompt improvement",
                        "Improve this prompt for clarity & constraints: 'Write blog about AI.'",
                        ["Specify length, audience, tone", "Add acceptance criteria"], 0.4),
                TaskDef("i2", "intermediate", "Chain planning",
                        "Given the goal 'launch a landing page', list a step-by-step plan with 8 steps.",
                        ["Numbered steps", "Add deliverables per step"], 0.4),
                TaskDef("i3", "intermediate", "Data transform",
                        "Convert this CSV to JSON with keys: name, email, score.",
                        ["Validate headers", "Return JSON only"], 0.4),
            ],
            "advanced": [
                TaskDef("a1", "advanced", "Few-shot prompt",
                        "Design a few-shot prompt that converts noisy Q&A into clean FAQ entries.",
                        ["Include 2-3 examples", "Define output schema"], 0.8),
                TaskDef("a2", "advanced", "Eval rubric",
                        "Create a rubric (0-1) for grading short product descriptions against clarity & persuasiveness.",
                        ["3 criteria", "weighting sum=1.0"], 0.8),
            ],
            "jailbreak": [
                TaskDef("j1", "jailbreak", "Red-team (safe)",
                        "Find a harmless way to detect and block jailbreak-style prompts without violating user rights.",
                        ["List patterns", "Provide 3 detection rules"], 1.2),
                TaskDef("j2", "jailbreak", "Safety prompt",
                        "Write a system prompt that enforces strict safety on disallowed content with fallback phrasing.",
                        ["Concise policy bullets", "Refusal + redirection script"], 1.2),
            ],
        }

    def _sample_tasks(self, level: str, k: int = 5) -> List[TaskDef]:
        bank = list(self._catalog.get(level, []))
        # simple rotate; if k > available, cycle
        if not bank:
            return []
        out: List[TaskDef] = []
        idx = int(datetime.now(timezone.utc).timestamp()) % len(bank)
        for n in range(k):
            out.append(bank[(idx + n) % len(bank)])
        return out

    def _latest_bundle(self, user_id: str, level: Optional[str]) -> Optional[Bundle]:
        # choose latest non-expired for this user (and level if specified)
        now = datetime.now(timezone.utc)
        candidates = [
            b for b in self._bundles.values()
            if b.user_id == user_id and b.expire_at > now and (level is None or b.level == level)
        ]
        if not candidates:
            return None
        return sorted(candidates, key=lambda b: b.expire_at, reverse=True)[0]

    def _task_by_id(self, level: str, task_id: str) -> Optional[TaskDef]:
        for t in self._catalog.get(level, []):
            if t.id == task_id:
                return t
        return None

    def _score(self, output: str, base: TaskDef) -> float:
        """
        Very light scoring for prototype:
        - length heuristic
        - presence of tips keywords (rough)
        Range clamp [0.3, 1.0]
        """
        length = len(output.strip())
        length_score = 1.0 if length >= 40 else 0.5 if length >= 10 else 0.3
        tip_bonus = 0.0
        low = base.title.lower()
        if "json" in base.prompt.lower() and ("{" in output and "}" in output):
            tip_bonus += 0.2
        if "bullets" in base.prompt.lower() and ("- " in output or "•" in output or "\n" in output):
            tip_bonus += 0.1
        score = min(1.0, max(0.3, length_score + tip_bonus))
        return score

# End of file
