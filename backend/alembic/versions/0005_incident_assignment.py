"""Add service ownership and incident assignment."""

from alembic import op
import sqlalchemy as sa

revision = "0005_incident_assignment"
down_revision = "0004_telemetry_resources"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("services", sa.Column("owner_team", sa.String(120), nullable=False, server_default="platform-oncall"))
    op.add_column("incidents", sa.Column("assigned_to", sa.String(120), nullable=True))


def downgrade():
    op.drop_column("incidents", "assigned_to")
    op.drop_column("services", "owner_team")
