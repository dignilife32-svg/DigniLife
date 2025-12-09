"""
Seed Task Types - Initialize 8 task types
"""
import sys
import os
import asyncio
from datetime import datetime
from uuid import uuid4

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.session import AsyncSessionLocal
from src.db.models import TaskType


TASK_TYPES = [
    {"name": "image_labeling", "display_name": "Image Labeling", "description": "Label and annotate images", "icon": "🖼️"},
    {"name": "text_annotation", "display_name": "Text Annotation", "description": "Classify and tag text", "icon": "📝"},
    {"name": "audio_transcription", "display_name": "Audio Transcription", "description": "Transcribe audio to text", "icon": "🎤"},
    {"name": "video_review", "display_name": "Video Review", "description": "Review video content", "icon": "🎥"},
    {"name": "data_validation", "display_name": "Data Validation", "description": "Verify data accuracy", "icon": "✅"},
    {"name": "content_moderation", "display_name": "Content Moderation", "description": "Flag inappropriate content", "icon": "🛡️"},
    {"name": "survey", "display_name": "Survey", "description": "Complete surveys", "icon": "📊"},
    {"name": "other", "display_name": "Other", "description": "Various tasks", "icon": "📦"},
]


async def seed_task_types():
    """Seed task types into database"""
    async with AsyncSessionLocal() as session:
        try:
            from sqlalchemy import select
            result = await session.execute(select(TaskType))
            existing = result.scalars().all()
            
            if len(existing) > 0:
                print(f"⚠️  Task types already exist ({len(existing)} found). Skipping seed.")
                return
            
            for task_type_data in TASK_TYPES:
                task_type = TaskType(
                    id=uuid4(),
                    name=task_type_data["name"],
                    display_name=task_type_data["display_name"],
                    description=task_type_data["description"],
                    icon=task_type_data["icon"],
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                session.add(task_type)
            
            await session.commit()
            print(f"✅ Successfully seeded {len(TASK_TYPES)} task types!")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error seeding task types: {e}")
            raise


if __name__ == "__main__":
    print("🌱 Seeding task types...")
    asyncio.run(seed_task_types())