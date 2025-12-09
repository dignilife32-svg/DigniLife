"""
Authentication Endpoints - FACE LIVENESS FIRST!
Register: Email + Face (password optional)
Login: Face FIRST (email/password fallback)
"""
from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.session import get_db
from src.db.models import User, Wallet, FaceLivenessLog, SubscriptionTier, UserRole
from src.schemas.user import UserCreate, UserLogin, UserResponse, Token
from src.core.security import (
    verify_password, 
    get_password_hash,
    create_access_token,
    create_refresh_token
)
from src.services.face_liveness import FaceLivenessDetector


router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register with Email + Face Liveness
    Password is OPTIONAL (for account recovery only)
    """
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Verify face liveness FIRST
    liveness_result = await FaceLivenessDetector.verify_liveness(
        image_data=user_data.face_image_base64,
        user_id=None,  # New user, no ID yet
    )
    
    if not FaceLivenessDetector.validate_liveness_result(liveness_result):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Face verification failed. Please try again with better lighting."
        )
    
    # Create user
    user = User(
        id=uuid4(),
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password) if user_data.password else None,
        full_name=user_data.full_name,
        phone_number=user_data.phone_number,
        role=UserRole.USER,
        subscription_tier=SubscriptionTier.FREE,
        is_active=True,
        is_verified=True,  # Auto-verified because face passed
        face_verified=True,  # Face is verified
        face_embedding=user_data.face_image_base64[:500],  # Store partial for matching (or use hash)
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(user)
    
    # Create wallet
    wallet = Wallet(
        id=uuid4(),
        user_id=user.id,
        balance_usd=0,
        pending_usd=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(wallet)
    
    # Log face verification
    face_log = FaceLivenessLog(
        id=uuid4(),
        user_id=user.id,
        is_live=True,
        confidence_score=liveness_result.get("confidence", 95),
        detection_details=liveness_result.get("details", {}),
        created_at=datetime.utcnow(),
    )
    db.add(face_log)
    
    await db.commit()
    await db.refresh(user)
    
    return user


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with Face Liveness FIRST
    Email/Password as fallback only
    """
    user = None
    login_method = "face"
    
    # PRIMARY: Face Liveness Login
    liveness_result = await FaceLivenessDetector.verify_liveness(
        image_data=login_data.face_image_base64,
        user_id=None,
    )
    
    if FaceLivenessDetector.validate_liveness_result(liveness_result):
        # Face verified! Now find user by face matching
        # In production, you'd use face recognition to match face_embedding
        # For now, if they provide email, use that
        if login_data.email:
            result = await db.execute(select(User).where(User.email == login_data.email))
            user = result.scalar_one_or_none()
            
            if user and user.face_verified:
                # Log successful face login
                face_log = FaceLivenessLog(
                    id=uuid4(),
                    user_id=user.id,
                    is_live=True,
                    confidence_score=liveness_result.get("confidence", 95),
                    detection_details=liveness_result.get("details", {}),
                    created_at=datetime.utcnow(),
                )
                db.add(face_log)
                login_method = "face"
    
    # FALLBACK: Email + Password (if face fails or not available)
    if not user and login_data.email and login_data.password:
        result = await db.execute(select(User).where(User.email == login_data.email))
        user = result.scalar_one_or_none()
        
        if user and user.hashed_password:
            if not verify_password(login_data.password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password",
                )
            login_method = "email_password"
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account uses face login only. Password not set.",
            )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login failed. Face not recognized or credentials invalid.",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    user.login_count += 1
    await db.commit()
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "login_method": login_method,
    }


@router.post("/login/face-only", response_model=Token)
async def login_face_only(
    face_image: str,
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Pure face login (no password needed)
    """
    # Verify face
    liveness_result = await FaceLivenessDetector.verify_liveness(
        image_data=face_image,
        user_id=None,
    )
    
    if not FaceLivenessDetector.validate_liveness_result(liveness_result):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Face verification failed"
        )
    
    # Get user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user or not user.face_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or face not registered"
        )
    
    # Log face login
    face_log = FaceLivenessLog(
        id=uuid4(),
        user_id=user.id,
        is_live=True,
        confidence_score=liveness_result.get("confidence", 95),
        detection_details=liveness_result.get("details", {}),
        created_at=datetime.utcnow(),
    )
    db.add(face_log)
    
    user.last_login_at = datetime.utcnow()
    user.login_count += 1
    await db.commit()
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "login_method": "face_only",
    }