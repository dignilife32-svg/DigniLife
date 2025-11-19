# src/ai/langdetect.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, List
import re
import json
from pathlib import Path

# --- Unicode blocks (quick heuristics) ---
MM_RANGE = (0x1000, 0x109F)        # Myanmar
ZAWGYI_HINTS = [u"\u1031\u103b", u"\u103b\u1031"]  # basic zg patterns

LATIN_RANGE = (0x0041, 0x024F)     # Latin + ext (rough screen)

def _ratio(pred:list[int], lo:int, hi:int) -> float:
    total = len(pred) or 1
    inside = sum(1 for cp in pred if lo <= cp <= hi)
    return inside/total

def _cp_list(s:str) -> List[int]:
    return [ord(ch) for ch in s if not ch.isspace()]

@dataclass
class LangResult:
    code: str         # ISO-ish (en, my, cnh, lus, etc.)
    confidence: float # 0..1
    method: str       # "unicode", "dict", "profile", "fallback"

class LangDetect:
    """
    Lightweight offline detector.
    - Hierarchy: unicode block -> custom lexicon -> profiles -> fallback
    - Profiles are simple JSONs you can extend (admin-updatable later).
    """
    def __init__(self, profiles_dir: Optional[Path] = None) -> None:
        self.profiles: Dict[str, Dict] = {}
        self.lexicon: Dict[str, List[str]] = {
            # quick keywords (extend anytime)
            "cnh": ["hmai", "na", "kan", "bang", "cang", "lei"],   # Hakha Chin hints
            "lus": ["mizo", "awm", "chuan", "chu", "tih", "a"],    # Mizo/Lushai
            "my":  ["မြန်မာ", "ဟုတ်တယ်", "ကိုယ့်", "နေကောင်း"],        # Burmese words
        }
        self._load_profiles(profiles_dir)

    def _load_profiles(self, profiles_dir: Optional[Path]) -> None:
        # Optional admin-supplied ngram/frequency profiles (future)
        if not profiles_dir:
            profiles_dir = Path(__file__).parent / "lang_profiles"
        if profiles_dir.exists():
            for p in profiles_dir.glob("*.json"):
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    code = data.get("code")
                    if code:
                        self.profiles[code] = data
                except Exception:
                    pass

    # --- Public API ---
    def detect(self, text: str) -> LangResult:
        s = (text or "").strip()
        if not s:
            return LangResult(code="en", confidence=0.50, method="fallback")

        cps = _cp_list(s)

        # 1) Strong unicode block: Myanmar
        mm_ratio = _ratio(cps, *MM_RANGE)
        if mm_ratio > 0.40:
            # try to distinguish Zawgyi (rough) vs Unicode if needed
            zg = any(h in s for h in ZAWGYI_HINTS)
            return LangResult(code="my", confidence=0.95 if not zg else 0.85, method="unicode")

        # 2) Latin script — check lexicon hints for cnh/lus first
        lat_ratio = _ratio(cps, *LATIN_RANGE)
        if lat_ratio > 0.60:
            for code, hints in self.lexicon.items():
                if code in ("cnh", "lus"):
                    for h in hints:
                        if re.search(rf"\b{re.escape(h)}\b", s, flags=re.IGNORECASE):
                            return LangResult(code=code, confidence=0.80, method="dict")

        # 3) Profiles (if later provided). Here we only showcase structure.
        best: Tuple[str, float] | None = None
        for code, prof in self.profiles.items():
            # simple token overlap score (placeholder, can be upgraded to n-gram)
            vocab = set(prof.get("vocab", [])[:500])
            if not vocab:
                continue
            toks = set(re.findall(r"[A-Za-z\u1000-\u109F]+", s.lower()))
            score = len(toks & vocab) / max(1, len(toks))
            conf = min(0.9, 0.5 + score)
            if not best or conf > best[1]:
                best = (code, conf)
        if best:
            return LangResult(code=best[0], confidence=best[1], method="profile")

        # 4) Fallback default
        # If mostly Latin and contains typical English stop words → en
        if lat_ratio > 0.60 and re.search(r"\b(the|and|is|are|you|to|of)\b", s, re.I):
            return LangResult(code="en", confidence=0.75, method="heuristic")

        # Unknown — default to EN but low confidence
        return LangResult(code="en", confidence=0.55, method="fallback")
