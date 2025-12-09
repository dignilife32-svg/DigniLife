"""
DigniLife Platform - Earning Calculation Engine
Handles all earning calculations with bonuses
"""
from decimal import Decimal
from typing import Dict

from src.db.models import SubscriptionTier


class EarningEngine:
    """Calculate user earnings with all bonuses"""
    
    # Tier multipliers
    TIER_MULTIPLIERS = {
        SubscriptionTier.FREE: Decimal("1.0"),      # No bonus
        SubscriptionTier.PRO: Decimal("1.1"),       # 10% more
        SubscriptionTier.PREMIUM: Decimal("1.2"),   # 20% more
    }
    
    @classmethod
    def calculate_earning(
        cls,
        base_reward: Decimal,
        ai_score: Decimal,
        completion_time_seconds: int,
        expected_time_seconds: int,
        user_tier: SubscriptionTier,
        current_streak: int,
    ) -> Dict[str, Decimal]:
        """
        Calculate total earning with all bonuses
        
        Args:
            base_reward: Base task reward in USD
            ai_score: AI validation score (0-100)
            completion_time_seconds: Time taken to complete
            expected_time_seconds: Expected completion time
            user_tier: User's subscription tier
            current_streak: User's current streak in days
        
        Returns:
            dict with breakdown of earning calculation
        """
        # Quality bonus (up to 20% for perfect score)
        quality_bonus = (ai_score / Decimal("100")) * base_reward * Decimal("0.2")
        
        # Speed bonus (up to 10% for fast completion)
        speed_bonus = cls._calculate_speed_bonus(
            base_reward, 
            completion_time_seconds, 
            expected_time_seconds
        )
        
        # Apply tier multiplier
        tier_mult = cls.TIER_MULTIPLIERS.get(user_tier, Decimal("1.0"))
        subtotal = (base_reward + quality_bonus + speed_bonus) * tier_mult
        
        # Streak bonus (1% per day, max 30%)
        streak_percentage = min(Decimal(current_streak) * Decimal("0.01"), Decimal("0.3"))
        streak_bonus = streak_percentage * base_reward
        
        # Total earning
        total_earning = subtotal + streak_bonus
        
        return {
            "base_reward": base_reward,
            "quality_bonus": quality_bonus,
            "speed_bonus": speed_bonus,
            "tier_multiplier": tier_mult,
            "streak_bonus": streak_bonus,
            "total_earning": total_earning,
        }
    
    @staticmethod
    def _calculate_speed_bonus(
        base_reward: Decimal,
        completion_time: int,
        expected_time: int
    ) -> Decimal:
        """Calculate speed bonus (faster = more bonus)"""
        if completion_time >= expected_time:
            return Decimal("0")
        
        # Calculate how much faster (0.0 to 1.0)
        time_saved = expected_time - completion_time
        speed_factor = Decimal(time_saved) / Decimal(expected_time)
        
        # Max 10% bonus for 50% faster completion
        speed_bonus = min(speed_factor * Decimal("0.2"), Decimal("0.1")) * base_reward
        
        return speed_bonus


class WithdrawalFeeCalculator:
    """Calculate withdrawal fees based on tier (AUTO-CUT)"""
    
    FEE_RATES = {
        SubscriptionTier.FREE: Decimal("0.15"),     # 15%
        SubscriptionTier.PRO: Decimal("0.10"),      # 10%
        SubscriptionTier.PREMIUM: Decimal("0.05"),  # 5%
    }
    
    @classmethod
    def calculate_fee(
        cls,
        gross_amount: Decimal,
        user_tier: SubscriptionTier,
    ) -> Dict[str, Decimal]:
        """
        Calculate withdrawal fee (auto-cut)
        
        Args:
            gross_amount: Amount before fees
            user_tier: User's subscription tier
        
        Returns:
            dict with fee breakdown
        """
        fee_rate = cls.FEE_RATES.get(user_tier, Decimal("0.15"))
        fee_amount = gross_amount * fee_rate
        net_amount = gross_amount - fee_amount
        
        return {
            "gross_amount": gross_amount,
            "fee_amount": fee_amount,
            "fee_percentage": fee_rate * Decimal("100"),
            "net_amount": net_amount,
            "tier": user_tier.value,
        }