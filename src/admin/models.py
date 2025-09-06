from typing import Dict

# Summary schema format
UserEarnings = Dict[str, float]  # e.g. {"usd": 12.50, "minutes": 60, ...}
TaskStats = Dict[str, int]       # e.g. {"read_aloud": 4, "qr_proof": 2, ...}
