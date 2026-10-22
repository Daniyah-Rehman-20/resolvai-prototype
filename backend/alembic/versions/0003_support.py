"""Persistent owner-scoped customer support intake."""
from alembic import op
import sqlalchemy as sa
revision = "0003_support"
down_revision = "0002_auth"
branch_labels = None
depends_on = None


def timestamps():
    return [sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False)]


def upgrade():
    op.create_table("support_conversations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("channel", sa.String(10), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("recording_consent", sa.Boolean(), nullable=False),
        sa.Column("consent_at", sa.DateTime(timezone=True)), *timestamps())
    op.create_index("ix_support_conversations_owner_id", "support_conversations", ["owner_id"])
    op.create_table("support_messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("support_conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(12), nullable=False), sa.Column("content", sa.Text(), nullable=False),
        sa.Column("mode", sa.String(32), nullable=False), sa.Column("sources", sa.JSON(), nullable=False), *timestamps())
    op.create_index("ix_support_messages_conversation_id", "support_messages", ["conversation_id"])
    op.create_table("support_queries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("support_conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("message_id", sa.String(36), sa.ForeignKey("support_messages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False), sa.Column("status", sa.String(32), nullable=False),
        sa.Column("facts", sa.JSON(), nullable=False),
        sa.Column("reviewer_note", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.String(36), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True), *timestamps())
    op.create_index("ix_support_queries_conversation_id", "support_queries", ["conversation_id"])


def downgrade():
    op.drop_table("support_queries")
    op.drop_table("support_messages")
    op.drop_table("support_conversations")
