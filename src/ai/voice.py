# src/ai/voice.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Optional
import base64, hashlib, os, time
from collections import defaultdict, deque

VOICE_PROVIDER = os.getenv("VOICE_PROVIDER", "dev").lower()
VOICE_RATE_PER_MIN = int(os.getenv("VOICE_RATE_PER_MIN", "8"))
VOICE_MAX_BYTES = int(os.getenv("VOICE_MAX_BYTES", str(2_000_000)))  # ~2MB

_rl_user: dict[str, deque] = defaultdict(deque)
_rl_dev: dict[str, deque] = defaultdict(deque)

def _enforce_rl(user_id: str, device_id: str) -> None:
    now = time.time(); window = 60.0
    dq = _rl_user[user_id]
    while dq and now - dq[0] > window: dq.popleft()
    if len(dq) >= VOICE_RATE_PER_MIN: raise RuntimeError("RATE_LIMIT_USER")
    dq.append(now)
    dq2 = _rl_dev[device_id]
    while dq2 and now - dq2[0] > window: dq2.popleft()
    if len(dq2) >= VOICE_RATE_PER_MIN: raise RuntimeError("RATE_LIMIT_DEVICE")
    dq2.append(now)

def _b64_to_bytes(b64: str) -> bytes:
    try:
        raw = base64.b64decode(b64, validate=True)
    except Exception as e:
        raise ValueError("BAD_BASE64") from e
    if len(raw) > VOICE_MAX_BYTES:
        raise ValueError("AUDIO_TOO_LARGE")
    return raw

@dataclass
class ASROut:
    transcript: str
    lang: str
    confidence: float

class DevMockASR:
    """Deterministic ASR mock – good for dev; replace with real SDK in ExternalASR."""
    def transcribe(self, audio_b64: str) -> ASROut:
        raw = _b64_to_bytes(audio_b64)
        h = hashlib.sha256(raw).hexdigest()
        # map hash → fake words/lang
        words = ["scan qr", "location check", "voice three words", "image label", "text tag"]
        pick = int(h[:2], 16) % len(words)
        # naive 'language' guess by byte entropy
        ent = sum(bin(b).count("1") for b in raw[:4096]) / max(1, len(raw[:4096])*8)
        lang = "en" if ent > 0.45 else "my"
        conf = 0.88 if pick in (0,1,2) else 0.75
        return ASROut(transcript=words[pick], lang=lang, confidence=conf)

class ExternalASR:
    """Skeleton to integrate real ASR (e.g., Whisper, Vosk, GCP STT)."""
    def transcribe(self, audio_b64: str) -> ASROut:
        raise NotImplementedError("Wire your real ASR here")

def get_asr():
    return ExternalASR() if VOICE_PROVIDER in {"external","prod","sdk"} else DevMockASR()

def voice_understand(user_id: str, device_id: str, audio_b64: str) -> ASROut:
    _enforce_rl(user_id, device_id)
    asr = get_asr()
    return asr.transcribe(audio_b64)

def map_transcript_to_hint(text: str) -> str | None:
    t = (text or "").lower()
    if "qr" in t: return "scan_qr"
    if "location" in t or "geo" in t or "map" in t: return "geo_ping"
    if "voice" in t or "three" in t or "3 words" in t: return "voice_3words"
    if "image" in t or "label" in t: return "image_label"
    if "text" in t or "tag" in t: return "text_tag"
    return None
