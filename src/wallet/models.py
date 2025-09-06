# src/wallet/models.py
from pydantic import BaseModel

class UserCapabilities(BaseModel):
    # Voice-first (စာမဖတ်တတ်/မြင်စာနည်း/အမြင်အာရုံအခက်အခဲ users အတွက်)
    prefers_voice: bool = True
    # Accessibility options (ယခင်/အနာဂတ် feature တွေအတွက် flags)
    prefers_large_text: bool = False
    prefers_high_contrast: bool = False
    limited_motor: bool = False
