"""add_missing_tables

Revision ID: d010c81662bc
Revises: 5fa292df3992
Create Date: 2026-03-23 08:52:48.494371

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd010c81662bc'
down_revision: Union[str, Sequence[str], None] = '5fa292df3992'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('refresh_tokens',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('jti', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('expires_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('revoked', sa.BOOLEAN(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], name=op.f('refresh_tokens_user_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('refresh_tokens_pkey')),
    sa.UniqueConstraint('jti', name=op.f('refresh_tokens_jti_key'))
    )

    op.create_table('social_links',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('platform', sa.VARCHAR(), nullable=False),
    sa.Column('url', sa.VARCHAR(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], name=op.f('social_links_user_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('social_links_pkey'))
    )
    op.create_index(op.f('ix_social_links_id'), 'social_links', ['id'], unique=False)

    op.create_table('email_verifications',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('token', sa.VARCHAR(), nullable=False),
    sa.Column('expires_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('used', sa.BOOLEAN(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], name=op.f('email_verifications_user_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('email_verifications_pkey')),
    sa.UniqueConstraint('token', name=op.f('email_verifications_token_key'))
    )

    op.create_table('password_resets',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('token', sa.VARCHAR(), nullable=False),
    sa.Column('expires_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('used', sa.BOOLEAN(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], name=op.f('password_resets_user_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('password_resets_pkey')),
    sa.UniqueConstraint('token', name=op.f('password_resets_token_key'))
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('password_resets')
    op.drop_table('email_verifications')
    op.drop_index(op.f('ix_social_links_id'), table_name='social_links')
    op.drop_table('social_links')
    op.drop_table('refresh_tokens')
