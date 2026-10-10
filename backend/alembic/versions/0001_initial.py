"""initial schema"""
from alembic import op
revision="0001"; down_revision=None; branch_labels=None; depends_on=None
def upgrade():
    from app.db.base import Base
    from app.models import domain  # noqa
    bind=op.get_bind()
    tables = [getattr(domain, name).__table__ for name in (
        "Customer", "Order", "Transaction", "Investigation", "ApprovalRequest",
        "Dispute", "Document", "AuditEvent",
    )]
    Base.metadata.create_all(bind, tables=tables)
def downgrade():
    from app.db.base import Base
    from app.models import domain
    bind=op.get_bind()
    tables = [getattr(domain, name).__table__ for name in (
        "Customer", "Order", "Transaction", "Investigation", "ApprovalRequest",
        "Dispute", "Document", "AuditEvent",
    )]
    Base.metadata.drop_all(bind, tables=tables)
