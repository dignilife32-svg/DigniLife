# src/realtime/ws.py
from __future__ import annotations
import json
import asyncio
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from redis.asyncio import from_url
from src.config import REDIS_URL

ws_router = APIRouter()

@ws_router.websocket("/ws/earn")
async def ws_earn(websocket: WebSocket, user_id: Optional[str] = Query(default=None)):
    """
    Connect like: ws://host/ws/earn?user_id=u123
    Intended for dashboards/power users (mobile uses polling).
    """
    await websocket.accept()
    if not user_id:
        await websocket.send_json({"type": "error", "detail": "user_id is required"})
        await websocket.close()
        return

    try:
        redis = from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        # subscribe to this user's channel
        channel_name = f"user:{user_id}:earn_updates"
        pubsub = redis.pubsub()
        await pubsub.subscribe(channel_name)

        # send hello
        await websocket.send_json({"type": "hello", "channel": channel_name})

        # read loop with small keepalive
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message.get("type") == "message":
                    payload = message.get("data")
                    try:
                        data = json.loads(payload)
                    except Exception:
                        data = {"type": "raw", "payload": payload}
                    await websocket.send_json(data)
                # keepalive ping every few seconds
                await asyncio.sleep(0.1)
        except WebSocketDisconnect:
            pass
        finally:
            try:
                await pubsub.unsubscribe(channel_name)
                await pubsub.close()
                await redis.close()
            except Exception:
                pass

    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "detail": str(e)})
        finally:
            await websocket.close()
