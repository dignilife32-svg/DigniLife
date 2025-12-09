"""
Device Management Endpoints
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from src.db.session import get_db
from src.db.models import User
from src.core.deps import get_current_active_user
from src.services.device_manager import DeviceManager


router = APIRouter()


class DeviceRegistration(BaseModel):
    device_id: str
    device_name: str
    device_type: str  # mobile, tablet, desktop
    os: str
    browser: str


class DeviceChangeRequest(BaseModel):
    reason: str


@router.post("/register")
async def register_device(
    device_info: DeviceRegistration,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Register user's device (one device per user)
    """
    # Get IP address
    ip_address = request.client.host
    
    device_data = {
        "device_id": device_info.device_id,
        "device_name": device_info.device_name,
        "device_type": device_info.device_type,
        "os": device_info.os,
        "browser": device_info.browser,
        "ip_address": ip_address,
    }
    
    device = await DeviceManager.register_device(
        user_id=current_user.id,
        device_info=device_data,
        db=db
    )
    
    return {
        "message": "Device registered successfully",
        "device_id": device.device_id,
        "device_name": device.device_name,
        "registered_at": device.registered_at,
    }


@router.get("/my-device")
async def get_my_device(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user's registered device
    """
    device = await DeviceManager.get_user_device(
        user_id=current_user.id,
        db=db
    )
    
    if not device:
        return {
            "has_device": False,
            "message": "No device registered yet"
        }
    
    return {
        "has_device": True,
        "device_id": device.device_id,
        "device_name": device.device_name,
        "device_type": device.device_type,
        "os": device.os,
        "registered_at": device.registered_at,
        "last_seen_at": device.last_seen_at,
    }


@router.post("/request-change")
async def request_device_change(
    change_request: DeviceChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Request to change registered device
    """
    result = await DeviceManager.request_device_change(
        user_id=current_user.id,
        reason=change_request.reason,
        db=db
    )
    
    return result