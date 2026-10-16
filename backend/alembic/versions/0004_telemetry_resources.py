"""Add resource and heartbeat telemetry."""

from alembic import op
import sqlalchemy as sa

revision = "0004_telemetry_resources"
down_revision = "0003_recovery_tracking"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("telemetry_samples", sa.Column("cpu_usage", sa.Float(), nullable=False, server_default="0"))
    op.add_column("telemetry_samples", sa.Column("memory_usage", sa.Float(), nullable=False, server_default="0"))
    op.add_column("telemetry_samples", sa.Column("request_volume", sa.Float(), nullable=False, server_default="0"))
    op.add_column("telemetry_samples", sa.Column("heartbeat_ok", sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade():
    op.drop_column("telemetry_samples", "heartbeat_ok")
    op.drop_column("telemetry_samples", "request_volume")
    op.drop_column("telemetry_samples", "memory_usage")
    op.drop_column("telemetry_samples", "cpu_usage")
