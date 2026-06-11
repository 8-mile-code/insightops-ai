"""fix dataset validated_at column type

Revision ID: 3a0390564cb4
Revises: 63dc1b828807
Create Date: 2026-06-11 15:57:12.819937

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '3a0390564cb4'
down_revision: Union[str, Sequence[str], None] = '63dc1b828807'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
