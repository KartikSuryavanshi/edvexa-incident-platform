"""Track simulated recovery outcomes."""

from alembic import op
import sqlalchemy as sa

revision = "0003_recovery_tracking"
down_revision = "0002_incident_engine"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("recovery_actions", sa.Column("last_error", sa.Text(), nullable=True))
    op.add_column("recovery_actions", sa.Column("duration_ms", sa.Integer(), nullable=True))
    op.add_column("recovery_actions", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column("recovery_actions", "approved_at")
    op.drop_column("recovery_actions", "duration_ms")
    op.drop_column("recovery_actions", "last_error")
