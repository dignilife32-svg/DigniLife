# src/routers/ai_chat.py
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
import os
os.environ.setdefault("CUDA_VISIBLES", "") # force CPU for now
import torch
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    pipeline,
)

router = APIRouter(prefix="/v1", tags=["ai"])

# =========
# Schemas
# =========
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: Optional[str] = None
    messages: List[ChatMessage]


# =====================================
# Model bootstrap (load once at import)
# =====================================
_DEFAULT_MODEL = "qwen2.5-7b-instruct"
_tokenizer = None
_model = None
_generator = None
_device: str = "cpu"


def _init_model(model_name: str = _DEFAULT_MODEL):
    """
    Try to load on CUDA with float16. If that fails for ANY reason
    (architecture mismatch, out-of-memory, etc.), fall back to CPU.
    """
    global _tokenizer, _model, _generator, _device

    print("🧠 Initializing model:", model_name)
    _device = "cuda" if torch.cuda.is_available() else "cpu"
    if _device == "cuda":
        try:
            name = torch.cuda.get_device_name(0)
        except Exception:
            name = "(unknown CUDA device)"
        print(f"⚙️  CUDA available -> {name}")

    _tokenizer = AutoTokenizer.from_pretrained(model_name)

    try:
        # Preferred path — GPU half precision
        if _device == "cuda":
            _model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
            )
            _generator = pipeline(
                "text-generation",
                model=_model,
                tokenizer=_tokenizer,
                device_map="auto",
            )
        else:
            raise RuntimeError("force-cpu")  # go to CPU block directly
        print("✅ Model loaded on CUDA (fp16).")
    except Exception as e:
        # Robust CPU fallback
        print("⚠️ CUDA failed or not suitable, switching to CPU mode:", e)
        _device = "cpu"
        _model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
        )
        _generator = pipeline(
            "text-generation",
            model=_model,
            tokenizer=_tokenizer,
            device=-1,  # CPU
        )
        print("✅ Model loaded on CPU (fp32).")


# import-time init
try:
    _init_model(_DEFAULT_MODEL)
except Exception as e:
    # If even CPU failed, keep generator None; endpoint will return 503
    print("❌ Model initialization failed:", e)
    _generator = None


# =========================
# Helpers
# =========================
def _extract_last_user(messages: List[ChatMessage]) -> str:
    """
    Return the last 'user' role content; otherwise the last message content.
    """
    for m in reversed(messages):
        if (m.role or "").lower() == "user":
            return m.content
    return messages[-1].content if messages else ""


def _build_response(model: str, text: str) -> Dict[str, Any]:
    """
    OpenAI-like response envelope so the playground can read
    choices[0].message.content safely.
    """
    now = int(time.time())
    return {
        "id": f"chatcmpl-{now}",
        "created": now,
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }


# =========================
# Chat Endpoint
# =========================
@router.post("/chat")
async def chat(req: ChatRequest):
    global _generator

    if _generator is None:
        # Model failed to initialize
        raise HTTPException(status_code=503, detail="model_not_ready")

    model_name = req.model or _DEFAULT_MODEL
    user_input = (_extract_last_user(req.messages) or "").strip()
    if not user_input:
        raise HTTPException(status_code=422, detail="empty_input")

    try:
        # Generate
        result = _generator(
            user_input,
            max_new_tokens=256,
            temperature=0.7,
            top_p=0.95,
            do_sample=True,
        )
        # transformers text-generation pipeline returns
        # [{'generated_text': '<prompt><completion>'}]
        full = result[0]["generated_text"]
        # remove the prompt part once (front-most)
        reply = full.replace(user_input, "", 1).strip()
        return _build_response(model_name, reply)
    except Exception as e:
        print("✖️ Chat error:", e)
        raise HTTPException(status_code=500, detail=str(e))
