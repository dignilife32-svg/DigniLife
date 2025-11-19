# src/routers/voice.py
from __future__ import annotations
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, Field, field_validator
from starlette.concurrency import run_in_threadpool

from src.ai.voice import voice_understand, map_transcript_to_hint
from src.ai.assist import assist_once

router = APIRouter(prefix="/voice", tags=["voice"])

class VoiceIn(BaseModel):
    user_id: str = Field(..., min_length=3)
    device_id: str = Field(..., min_length=3)
    audio_b64: str
    locale: Optional[str] = None
    autocredit: bool = True  # pass to assist

    @field_validator("audio_b64")
    @classmethod
    def _len(cls, v: str) -> str:
        if len(v) < 64: raise ValueError("AUDIO_TOO_SHORT")
        return v

class VoiceOut(BaseModel):
    ok: bool
    transcript: str
    lang: str
    asr_confidence: float
    assist: Dict[str, Any]

@router.post("/submit", response_model=VoiceOut)
async def voice_submit(p: VoiceIn, req: Request) -> VoiceOut:
    try:
        asr = await run_in_threadpool(voice_understand, p.user_id, p.device_id, p.audio_b64)
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    task_hint = map_transcript_to_hint(asr.transcript)
    assist_payload = dict(
        user_id=p.user_id, device_id=p.device_id,
        audio_b64=p.audio_b64, locale=p.locale, task_hint=task_hint,
        auto_credit=p.autocredit
    )
    assist_res = await run_in_threadpool(assist_once, assist_payload)
    if not assist_res.get("ok"):
        raise HTTPException(status_code=400, detail=assist_res.get("reason","ASSIST_ERROR"))

    return VoiceOut(
        ok=True, transcript=asr.transcript, lang=asr.lang,
        asr_confidence=asr.confidence, assist=assist_res
    )
