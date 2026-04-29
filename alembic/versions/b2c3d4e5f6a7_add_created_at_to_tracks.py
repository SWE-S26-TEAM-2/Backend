"""add created_at to tracks

Revision ID: b2c3d4e5f6a7
Revises: a7c2d9e4f6b1
Create Date: 2026-04-29

"""
from typing import Union, Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a7c2d9e4f6b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tracks",
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("tracks", "created_at")
