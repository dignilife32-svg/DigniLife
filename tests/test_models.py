"""
Test Database Models
"""
import pytest
from datetime import datetime
from uuid import uuid4

from src.db.models import (
    User, UserDevice, Task, Submission, Wallet, Transaction,
    SubscriptionTier, UserRole, TaskTypeEnum, TaskDifficultyEnum,
    SubmissionStatusEnum, TransactionTypeEnum, TransactionStatusEnum
)


@pytest.mark.asyncio
async def test_create_user(db_session):
    """Test creating a user"""
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed_password_here",
        full_name="Test User",
        subscription_tier=SubscriptionTier.FREE,
        role=UserRole.USER,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.subscription_tier == SubscriptionTier.FREE
    assert user.total_earnings_usd == 0


@pytest.mark.asyncio
async def test_user_device_relationship(db_session):
    """Test user-device relationship"""
    # Create user
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed",
        full_name="Test User",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.flush()
    
    # Create device
    device = UserDevice(
        id=uuid4(),
        user_id=user.id,
        device_fingerprint="test_fingerprint_123",
        device_name="Test Device",
        device_type="mobile",
        first_seen_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(device)
    await db_session.commit()
    
    assert device.user_id == user.id
    assert device.device_fingerprint == "test_fingerprint_123"


@pytest.mark.asyncio
async def test_create_wallet(db_session):
    """Test creating a wallet"""
    # Create user
    user = User(
        id=uuid4(),
        email="wallet@example.com",
        hashed_password="hashed",
        full_name="Wallet User",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.flush()
    
    # Create wallet
    wallet = Wallet(
        id=uuid4(),
        user_id=user.id,
        balance_usd=100.50,
        pending_usd=25.00,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(wallet)
    await db_session.commit()
    
    assert wallet.balance_usd == 100.50
    assert wallet.pending_usd == 25.00


@pytest.mark.asyncio
async def test_subscription_tiers(db_session):
    """Test subscription tier enum"""
    users = []
    
    for tier in [SubscriptionTier.FREE, SubscriptionTier.PRO, SubscriptionTier.PREMIUM]:
        user = User(
            id=uuid4(),
            email=f"{tier.value}@example.com",
            hashed_password="hashed",
            full_name=f"{tier.value} User",
            subscription_tier=tier,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        users.append(user)
        db_session.add(user)
    
    await db_session.commit()
    
    assert len(users) == 3
    assert users[0].subscription_tier == SubscriptionTier.FREE
    assert users[1].subscription_tier == SubscriptionTier.PRO
    assert users[2].subscription_tier == SubscriptionTier.PREMIUM