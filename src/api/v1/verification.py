"""
User Verification Endpoints (KYC & Face Liveness)
UPDATED: Flexible ID system - accepts any ID type
"""
from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from enum import Enum

from src.db.session import get_db
from src.db.models import User, FaceLivenessLog
from src.core.deps import get_current_active_user
from src.services.face_liveness import FaceLivenessDetector


router = APIRouter()


class IDTypeEnum(str, Enum):
    """Supported ID types"""
    NATIONAL_ID = "national_id"
    PASSPORT = "passport"
    UN_CARD = "un_card"
    COMMUNITY_CARD = "community_card"
    DRIVER_LICENSE = "driver_license"
    REFUGEE_ID = "refugee_id"
    VOTER_ID = "voter_id"
    OTHER = "other"


class KYCSubmission(BaseModel):
    """
    Flexible KYC - Accept ANY valid ID
    NO proof of address required
    """
    full_name: str
    date_of_birth: str  # YYYY-MM-DD format
    
    # Flexible ID system
    id_type: IDTypeEnum
    id_number: str
    id_issuing_country: str  # ISO country code (MM, TH, etc)
    id_expiry_date: Optional[str] = None  # Some IDs don't expire
    
    # Optional: If ID type is "other", specify what it is
    id_type_other: Optional[str] = None


class FaceLivenessCheck(BaseModel):
    image_base64: str  # Base64 encoded selfie


@router.post("/kyc/submit")
async def submit_kyc(
    kyc_data: KYCSubmission,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Submit KYC information - FLEXIBLE ID SYSTEM
    ✅ Accepts: National ID, Passport, UN Card, Community Card, etc.
    ❌ NO proof of address required
    ❌ NO company documents required
    """
    if current_user.kyc_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="KYC already verified"
        )
    
    # Validate ID type
    id_type_display = kyc_data.id_type.value
    if kyc_data.id_type == IDTypeEnum.OTHER and kyc_data.id_type_other:
        id_type_display = kyc_data.id_type_other
    
    # Store KYC data
    current_user.kyc_data = {
        "full_name": kyc_data.full_name,
        "date_of_birth": kyc_data.date_of_birth,
        
        # Flexible ID information
        "id_type": kyc_data.id_type.value,
        "id_type_display": id_type_display,
        "id_number": kyc_data.id_number,
        "id_issuing_country": kyc_data.id_issuing_country,
        "id_expiry_date": kyc_data.id_expiry_date,
        
        "submitted_at": datetime.utcnow().isoformat(),
        "status": "pending_review",
        "verification_method": "simple_kyc",  # Simple = ID + Face only
    }
    
    current_user.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "message": "KYC information submitted successfully",
        "status": "pending_review",
        "estimated_review_time": "24-48 hours",
        "id_type_accepted": id_type_display,
        "next_step": "Complete face verification to activate your account"
    }


@router.post("/face/verify")
async def verify_face_liveness(
    face_data: FaceLivenessCheck,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Verify face liveness (anti-spoofing)
    This is the PRIMARY verification method
    """
    # Perform liveness detection
    liveness_result = await FaceLivenessDetector.verify_liveness(
        image_data=face_data.image_base64,
        user_id=current_user.id,
    )
    
    # Log the check
    log = FaceLivenessLog(
        id=uuid4(),
        user_id=current_user.id,
        is_live=liveness_result.get("is_live", False),
        confidence_score=liveness_result.get("confidence", 0),
        detection_details=liveness_result.get("details", {}),
        created_at=datetime.utcnow(),
    )
    db.add(log)
    
    # Validate result
    passed = FaceLivenessDetector.validate_liveness_result(liveness_result)
    
    if passed:
        # Update user verification status
        current_user.is_verified = True
        current_user.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "passed": passed,
        "is_live": liveness_result.get("is_live"),
        "confidence": liveness_result.get("confidence"),
        "message": "✅ Face verification successful! Your account is now verified." if passed else "❌ Face verification failed. Please try again in good lighting.",
        "details": liveness_result.get("details", {}),
        "account_status": "verified" if passed else "pending_verification"
    }


@router.get("/status")
async def get_verification_status(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user's verification status
    """
    kyc_status = "not_submitted"
    id_type = None
    
    if current_user.kyc_data:
        kyc_status = current_user.kyc_data.get("status", "not_submitted")
        id_type = current_user.kyc_data.get("id_type_display")
    
    return {
        "face_verified": current_user.is_verified,
        "kyc_submitted": bool(current_user.kyc_data),
        "kyc_status": kyc_status,
        "kyc_verified": current_user.kyc_verified,
        "id_type": id_type,
        
        "verification_requirements": {
            "face_liveness": "✅ Required" if current_user.is_verified else "❌ Pending",
            "kyc_document": "✅ Submitted" if current_user.kyc_data else "❌ Not submitted",
            "proof_of_address": "❌ Not required",
            "company_license": "❌ Not required",
        },
        
        "can_start_earning": current_user.is_verified,
    }


@router.get("/accepted-ids")
async def get_accepted_id_types():
    """
    Get list of accepted ID types
    """
    return {
        "accepted_ids": [
            {
                "type": "national_id",
                "name": "National ID Card",
                "description": "Government-issued national identification card",
                "icon": "🪪"
            },
            {
                "type": "passport",
                "name": "Passport",
                "description": "International travel document",
                "icon": "📘"
            },
            {
                "type": "un_card",
                "name": "UN Card",
                "description": "United Nations identification card",
                "icon": "🌐"
            },
            {
                "type": "community_card",
                "name": "Community Card",
                "description": "Local community identification",
                "icon": "👥"
            },
            {
                "type": "driver_license",
                "name": "Driver's License",
                "description": "Government-issued driving permit",
                "icon": "🚗"
            },
            {
                "type": "refugee_id",
                "name": "Refugee ID",
                "description": "UNHCR refugee identification document",
                "icon": "🆔"
            },
            {
                "type": "voter_id",
                "name": "Voter ID",
                "description": "Electoral registration card",
                "icon": "🗳️"
            },
            {
                "type": "other",
                "name": "Other Valid ID",
                "description": "Any other government-issued or official ID",
                "icon": "📄"
            },
        ],
        "requirements": {
            "must_have": [
                "Face liveness verification (selfie)",
                "Valid ID (any type listed above)"
            ],
            "not_required": [
                "Proof of address",
                "Company registration",
                "Bank statements",
                "Utility bills"
            ]
        },
        "note": "We accept ANY valid identification document. Simple and inclusive verification!"
    }