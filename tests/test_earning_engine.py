"""
Test Earning Calculation Engine
"""
import pytest
from decimal import Decimal

from src.core.earning_engine import EarningEngine, WithdrawalFeeCalculator
from src.db.models import SubscriptionTier


def test_basic_earning_calculation():
    """Test basic earning calculation without bonuses"""
    result = EarningEngine.calculate_earning(
        base_reward=Decimal("10.00"),
        ai_score=Decimal("100"),
        completion_time_seconds=300,
        expected_time_seconds=300,
        user_tier=SubscriptionTier.FREE,
        current_streak=0,
    )
    
    assert result["base_reward"] == Decimal("10.00")
    assert result["quality_bonus"] == Decimal("2.00")  # 20% for perfect score
    assert result["speed_bonus"] == Decimal("0")  # No speed bonus
    assert result["tier_multiplier"] == Decimal("1.0")
    assert result["streak_bonus"] == Decimal("0")
    assert result["total_earning"] == Decimal("12.00")


def test_earning_with_pro_tier():
    """Test earning with PRO tier (10% multiplier)"""
    result = EarningEngine.calculate_earning(
        base_reward=Decimal("10.00"),
        ai_score=Decimal("100"),
        completion_time_seconds=300,
        expected_time_seconds=300,
        user_tier=SubscriptionTier.PRO,
        current_streak=0,
    )
    
    # (10 + 2) * 1.1 = 13.20
    assert result["tier_multiplier"] == Decimal("1.1")
    assert result["total_earning"] == Decimal("13.20")


def test_earning_with_premium_tier():
    """Test earning with PREMIUM tier (20% multiplier)"""
    result = EarningEngine.calculate_earning(
        base_reward=Decimal("10.00"),
        ai_score=Decimal("100"),
        completion_time_seconds=300,
        expected_time_seconds=300,
        user_tier=SubscriptionTier.PREMIUM,
        current_streak=0,
    )
    
    # (10 + 2) * 1.2 = 14.40
    assert result["tier_multiplier"] == Decimal("1.2")
    assert result["total_earning"] == Decimal("14.40")


def test_earning_with_speed_bonus():
    """Test earning with speed bonus"""
    result = EarningEngine.calculate_earning(
        base_reward=Decimal("10.00"),
        ai_score=Decimal("100"),
        completion_time_seconds=150,  # 50% faster
        expected_time_seconds=300,
        user_tier=SubscriptionTier.FREE,
        current_streak=0,
    )
    
    # Speed bonus should be 1.00 (10% of base for 50% faster)
    assert result["speed_bonus"] == Decimal("1.00")
    # (10 + 2 + 1) * 1.0 = 13.00
    assert result["total_earning"] == Decimal("13.00")


def test_earning_with_streak_bonus():
    """Test earning with streak bonus"""
    result = EarningEngine.calculate_earning(
        base_reward=Decimal("10.00"),
        ai_score=Decimal("100"),
        completion_time_seconds=300,
        expected_time_seconds=300,
        user_tier=SubscriptionTier.FREE,
        current_streak=10,  # 10 day streak = 10% bonus
    )
    
    # Streak bonus: 10 * 0.01 * 10 = 1.00
    assert result["streak_bonus"] == Decimal("1.00")
    # (10 + 2) * 1.0 + 1 = 13.00
    assert result["total_earning"] == Decimal("13.00")


def test_earning_max_streak_bonus():
    """Test earning with max streak bonus (30%)"""
    result = EarningEngine.calculate_earning(
        base_reward=Decimal("10.00"),
        ai_score=Decimal("100"),
        completion_time_seconds=300,
        expected_time_seconds=300,
        user_tier=SubscriptionTier.FREE,
        current_streak=50,  # Should cap at 30%
    )
    
    # Max streak bonus: 10 * 0.30 = 3.00
    assert result["streak_bonus"] == Decimal("3.00")
    # (10 + 2) * 1.0 + 3 = 15.00
    assert result["total_earning"] == Decimal("15.00")


def test_withdrawal_fee_free_tier():
    """Test withdrawal fee for FREE tier (15%)"""
    result = WithdrawalFeeCalculator.calculate_fee(
        gross_amount=Decimal("100.00"),
        user_tier=SubscriptionTier.FREE,
    )
    
    assert result["gross_amount"] == Decimal("100.00")
    assert result["fee_percentage"] == Decimal("15")
    assert result["fee_amount"] == Decimal("15.00")
    assert result["net_amount"] == Decimal("85.00")


def test_withdrawal_fee_pro_tier():
    """Test withdrawal fee for PRO tier (10%)"""
    result = WithdrawalFeeCalculator.calculate_fee(
        gross_amount=Decimal("100.00"),
        user_tier=SubscriptionTier.PRO,
    )
    
    assert result["fee_percentage"] == Decimal("10")
    assert result["fee_amount"] == Decimal("10.00")
    assert result["net_amount"] == Decimal("90.00")


def test_withdrawal_fee_premium_tier():
    """Test withdrawal fee for PREMIUM tier (5%)"""
    result = WithdrawalFeeCalculator.calculate_fee(
        gross_amount=Decimal("100.00"),
        user_tier=SubscriptionTier.PREMIUM,
    )
    
    assert result["fee_percentage"] == Decimal("5")
    assert result["fee_amount"] == Decimal("5.00")
    assert result["net_amount"] == Decimal("95.00")


def test_complex_earning_scenario():
    """Test complex earning scenario with all bonuses"""
    # Premium user, perfect score, 50% faster, 15 day streak
    result = EarningEngine.calculate_earning(
        base_reward=Decimal("20.00"),
        ai_score=Decimal("100"),
        completion_time_seconds=150,
        expected_time_seconds=300,
        user_tier=SubscriptionTier.PREMIUM,
        current_streak=15,
    )
    
    # Base: 20
    # Quality: 4 (20%)
    # Speed: 2 (10%)
    # Subtotal: (20 + 4 + 2) * 1.2 = 31.20
    # Streak: 20 * 0.15 = 3.00
    # Total: 34.20
    
    assert result["base_reward"] == Decimal("20.00")
    assert result["quality_bonus"] == Decimal("4.00")
    assert result["speed_bonus"] == Decimal("2.00")
    assert result["tier_multiplier"] == Decimal("1.2")
    assert result["streak_bonus"] == Decimal("3.00")
    assert result["total_earning"] == Decimal("34.20")