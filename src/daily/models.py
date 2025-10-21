from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class DailyTask(Base):
    __tablename__ = "daily_tasks"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)
    base_reward_usd = Column(Float, nullable=False, default=0.0)
    date = Column(Date, default=date.today)  # today’s task date
    is_variant = Column(Boolean, default=False)
    parent_code = Column(String(50), nullable=True)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DailyTask(code={self.code}, name={self.name}, reward={self.base_reward_usd})>"
