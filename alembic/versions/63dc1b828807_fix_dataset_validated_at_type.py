"""fix dataset validated_at type

Revision ID: 63dc1b828807
Revises: 67a2bc2b8272
Create Date: 2026-06-11 15:51:57.520557

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '63dc1b828807'
down_revision: Union[str, Sequence[str], None] = '67a2bc2b8272'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
