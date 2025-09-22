# -*- coding: utf-8 -*-
from __future__ import annotations
from fastapi import HTTPException

def _raise(status: int, code: str, message: str):
    raise HTTPException(status_code=status, detail={"code": code, "message": message})

def err_dup():         _raise(409, "ERR_DUP", "Duplicate submission.")
def err_rate():        _raise(429, "ERR_RATE", "Rate limit reached.")
def err_cap():         _raise(403, "ERR_CAP", "Daily earning cap reached.")
def err_quality_low(): _raise(422, "ERR_QUALITY_LOW", "Quality below threshold.")
def err_expired():     _raise(410, "ERR_EXPIRED", "Assignment expired or invalid.")
def err_badreq(msg):   _raise(400, "ERR_BAD_REQUEST", msg)


# src/utils/errors.py
from typing import Any, Optional
import logging
logger = logging.getLogger("app")

def fallback_log(context: str, err: Exception, extra: Optional[dict[str, Any]] = None) -> None:
    try:
        logger.exception("fallback: %s :: %s :: extra=%s", context, err, extra or {})
    except Exception:
        # logging အလုံခြုံ fallback
        print(f"[fallback] {context}: {err} extra={extra}")
