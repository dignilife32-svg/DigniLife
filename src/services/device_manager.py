"""
Device Management Service
One device per user - Security enforcement
"""
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from src.db.models import UserDevice


class DeviceManager:
    """
    Manage user devices - enforce one device per user
    """
    
    @staticmethod
    async def register_device(
        user_id: UUID,
        device_info: Dict[str, Any],
        db: AsyncSession
    ) -> UserDevice:
        """
        Register a new device for user
        
        Args:
            user_id: User ID
            device_info: Device information dict with:
                - device_id: Unique device identifier
                - device_name: Device name
                - device_type: mobile/tablet/desktop
                - os: Operating system
                - browser: Browser name
                - ip_address: IP address
        
        Returns:
            UserDevice object
        
        Raises:
            HTTPException: If user already has a device registered
        """
        # Check if user already has a device
        result = await db.execute(
            select(UserDevice).where(
                UserDevice.user_id == user_id,
                UserDevice.is_active == True
            )
        )
        existing_device = result.scalar_one_or_none()
        
        if existing_device:
            # Check if it's the same device
            if existing_device.device_id == device_info.get("device_id"):
                # Update last seen
                existing_device.last_seen_at = datetime.utcnow()
                existing_device.last_ip_address = device_info.get("ip_address")
                await db.commit()
                return existing_device
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only use DigniLife on one device. Please use your registered device or contact support to change devices.",
                    headers={"X-Device-Limit": "reached"}
                )
        
        # Register new device
        device = UserDevice(
            id=uuid4(),
            user_id=user_id,
            device_id=device_info.get("device_id"),
            device_name=device_info.get("device_name", "Unknown Device"),
            device_type=device_info.get("device_type", "unknown"),
            os=device_info.get("os"),
            browser=device_info.get("browser"),
            ip_address=device_info.get("ip_address"),
            last_ip_address=device_info.get("ip_address"),
            is_active=True,
            registered_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )
        
        db.add(device)
        await db.commit()
        await db.refresh(device)
        
        return device
    
    @staticmethod
    async def verify_device(
        user_id: UUID,
        device_id: str,
        db: AsyncSession
    ) -> bool:
        """
        Verify if device is registered and active for user
        
        Args:
            user_id: User ID
            device_id: Device identifier
            db: Database session
        
        Returns:
            True if device is valid, False otherwise
        """
        result = await db.execute(
            select(UserDevice).where(
                UserDevice.user_id == user_id,
                UserDevice.device_id == device_id,
                UserDevice.is_active == True
            )
        )
        device = result.scalar_one_or_none()
        
        if device:
            # Update last seen
            device.last_seen_at = datetime.utcnow()
            await db.commit()
            return True
        
        return False
    
    @staticmethod
    async def get_user_device(
        user_id: UUID,
        db: AsyncSession
    ) -> Optional[UserDevice]:
        """Get user's registered device"""
        result = await db.execute(
            select(UserDevice).where(
                UserDevice.user_id == user_id,
                UserDevice.is_active == True
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def request_device_change(
        user_id: UUID,
        reason: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Request to change device (creates support ticket)
        
        Args:
            user_id: User ID
            reason: Reason for device change
            db: Database session
        
        Returns:
            Dict with ticket information
        """
        from src.db.models import SupportTicket, TicketPriorityEnum, TicketStatusEnum
        
        # Create support ticket
        ticket = SupportTicket(
            id=uuid4(),
            user_id=user_id,
            subject="Device Change Request",
            description=f"User requested device change. Reason: {reason}",
            priority=TicketPriorityEnum.HIGH,
            status=TicketStatusEnum.OPEN,
            ticket_metadata={"type": "device_change", "reason": reason},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        db.add(ticket)
        await db.commit()
        await db.refresh(ticket)
        
        return {
            "ticket_id": str(ticket.id),
            "message": "Device change request submitted. Our team will review it within 24 hours.",
            "status": "pending_review"
        }