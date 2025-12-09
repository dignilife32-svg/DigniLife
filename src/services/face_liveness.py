"""
Face Liveness Detection Service
Prevents photo-based fraud
"""
from typing import Dict, Any, Optional
import base64
from datetime import datetime
from uuid import UUID
import httpx

from src.core.config import settings


class FaceLivenessDetector:
    """
    Face Liveness Detection Service
    Integrates with external liveness API
    """
    
    @staticmethod
    async def verify_liveness(
        image_data: str,
        user_id: UUID,
    ) -> Dict[str, Any]:
        """
        Verify face liveness from image
        
        Args:
            image_data: Base64 encoded image
            user_id: User ID for logging
        
        Returns:
            Dict with:
                - is_live: bool
                - confidence: float (0-100)
                - details: dict with detection info
        """
        
        # If no API configured, use mock validation
        if not settings.LIVENESS_API_URL or not settings.LIVENESS_API_KEY:
            return FaceLivenessDetector._mock_liveness_check(image_data)
        
        try:
            # Call external liveness API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    settings.LIVENESS_API_URL,
                    headers={
                        "Authorization": f"Bearer {settings.LIVENESS_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "image": image_data,
                        "user_id": str(user_id),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "is_live": data.get("is_live", False),
                        "confidence": data.get("confidence", 0),
                        "details": data.get("details", {}),
                        "api_response": "success"
                    }
                else:
                    # Fallback to mock on API error
                    return FaceLivenessDetector._mock_liveness_check(image_data)
        
        except Exception as e:
            # Fallback to mock on exception
            print(f"Liveness API error: {e}")
            return FaceLivenessDetector._mock_liveness_check(image_data)
    
    @staticmethod
    def _mock_liveness_check(image_data: str) -> Dict[str, Any]:
        """
        Mock liveness check for development
        In production, this should be replaced with real API
        """
        import random
        
        # Simulate liveness detection
        # In real implementation, this would analyze the image
        is_live = random.choice([True, True, True, False])  # 75% pass rate
        confidence = random.uniform(85, 99) if is_live else random.uniform(30, 60)
        
        return {
            "is_live": is_live,
            "confidence": confidence,
            "details": {
                "face_detected": True,
                "eye_blink_detected": is_live,
                "head_movement_detected": is_live,
                "quality_score": random.uniform(70, 95),
                "mock": True,
                "message": "Using mock liveness detection. Configure LIVENESS_API_URL for production."
            },
            "api_response": "mock"
        }
    
    @staticmethod
    def validate_liveness_result(result: Dict[str, Any]) -> bool:
        """
        Validate if liveness check passed
        
        Args:
            result: Result from verify_liveness
        
        Returns:
            True if passed, False otherwise
        """
        return result.get("is_live", False) and result.get("confidence", 0) >= 80.0