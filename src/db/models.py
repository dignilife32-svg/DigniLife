from __future__ import annotations
from datetime import date, datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, Boolean, Date, Text, UniqueConstraint, inspect
from sqlalchemy.orm import mapped_column, Mapped

from src.db.session import Base

# --- Daily tasks table (used by auto_injector) ---
class DailyTask(Base):
    __tablename__ = "daily_tasks"
    __table_args__ = (
        UniqueConstraint("date", "code", name="uq_daily_tasks_date_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # YYYY-MM-DD for which the task is valid
    date: Mapped[date] = mapped_column(Date, index=True)

    # short code/slug like "micro_reflect"
    code: Mapped[str] = mapped_column(String(64), index=True)

    # canonical category: micro | qr | geo | voice | visual | feedback | engine …
    category: Mapped[str] = mapped_column(String(32), index=True, default="micro")

    # payout to show (display only)
    display_value_usd: Mapped[float] = mapped_column(Float, default=0.0)

    # estimated time in seconds
    expected_time_sec: Mapped[int] = mapped_column(Integer, default=60)

    # user-facing instruction/prompt
    user_prompt: Mapped[str] = mapped_column(Text, default="")

    # optional json string of actions/extra config
    user_actions_json: Mapped[Optional[str]] = mapped_column(Text, default=None)

    # enabled?
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class AsDictMixin:
    def as_dict(self):
        i = inspect(self)
        return {c.key: getattr(self, c.key) for c in i.mapper.column_attrs}
    