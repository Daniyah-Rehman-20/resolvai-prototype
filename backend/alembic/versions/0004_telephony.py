"""Consent-gated phone linkage and durable recording queue."""
from alembic import op
import sqlalchemy as sa
revision = '0004_telephony'
down_revision = '0003_support'
branch_labels = None
depends_on = None


def timestamps():
    return [sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)]


def upgrade():
    op.create_table('phone_links',
        sa.Column('code_hash', sa.String(64), primary_key=True),
        sa.Column('owner_id', sa.String(36), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False), *timestamps())
    op.create_index('ix_phone_links_owner_id', 'phone_links', ['owner_id'])
    op.create_table('phone_calls',
        sa.Column('call_sid', sa.String(34), primary_key=True),
        sa.Column('owner_id', sa.String(36), nullable=False),
        sa.Column('conversation_id', sa.String(36), sa.ForeignKey('support_conversations.id', ondelete='CASCADE')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False), *timestamps())
    op.create_table('phone_recordings',
        sa.Column('recording_sid', sa.String(34), primary_key=True),
        sa.Column('call_sid', sa.String(34), sa.ForeignKey('phone_calls.call_sid', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('response', sa.Text()),
        sa.UniqueConstraint('call_sid', name='uq_phone_call_recording'), *timestamps())


def downgrade():
    op.drop_table('phone_recordings')
    op.drop_table('phone_calls')
    op.drop_table('phone_links')
