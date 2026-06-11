"""alter dataset validated_at to timestamptz

Revision ID: 5fe672b92091
Revises: 3a0390564cb4
Create Date: 2026-06-11 16:05:56.308131

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5fe672b92091'
down_revision: Union[str, Sequence[str], None] = '3a0390564cb4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "datasets",
        "validated_at",
        existing_type=sa.String(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
        postgresql_using="validated_at::timestamptz",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "datasets",
        "validated_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.String(),
        existing_nullable=True,
    )
