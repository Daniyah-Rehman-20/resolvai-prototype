"""Persistent users and revocable authentication sessions."""
from alembic import op
from app.models.auth import AuthSession, User

revision = "0002_auth"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    User.__table__.create(op.get_bind(), checkfirst=True)
    AuthSession.__table__.create(op.get_bind(), checkfirst=True)


def downgrade():
    AuthSession.__table__.drop(op.get_bind(), checkfirst=True)
    User.__table__.drop(op.get_bind(), checkfirst=True)
