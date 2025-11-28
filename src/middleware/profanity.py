#src/meddleware/profanity.py
import re
from typing import Tuple, List

# Minimal seed list (you can extend from config later)
SEED = [
    r"\bfuck\b", r"\bf\*+k\b", r"\bshit\b", r"\basshole\b", r"\bdamn\b",
    r"\bbitch\b", r"\bmotherf\w+\b", r"\bwtf\b"
]

# Compile once
PATTERNS: List[re.Pattern] = [re.compile(p, re.IGNORECASE) for p in SEED]

def _mask(m: re.Match) -> str:
    w = m.group(0)
    if len(w) <= 2: 
        return "*" * len(w)
    return w[0] + ("*" * (len(w)-2)) + w[-1]

def scrub(text: str) -> Tuple[str, int]:
    """
    Returns (clean_text, hits)
    - clean_text: words masked (f***, s**t)
    - hits: number of profane matches for severity/rate-limit heuristics
    """
    hits = 0
    def repl(m):
        nonlocal hits
        hits += 1
        return _mask(m)
    clean = text
    for pat in PATTERNS:
        clean = pat.sub(repl, clean)
    return clean, hits
