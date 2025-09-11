"""rewards + referrals

Revision ID: 81635815cbc1
Revises: 7ddc56c98c3f
Create Date: 2025-09-11 12:54:06.211570

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '81635815cbc1'
down_revision: Union[str, Sequence[str], None] = '7ddc56c98c3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
