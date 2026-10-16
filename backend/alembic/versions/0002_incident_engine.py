"""Add health checks and incident engine fields."""

from alembic import op
import sqlalchemy as sa

revision = "0002_incident_engine"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    incident_columns = {column["name"] for column in inspector.get_columns("incidents")}
    event_columns = {column["name"] for column in inspector.get_columns("incident_events")}
    if "deduplication_key" not in incident_columns:
        op.add_column("incidents", sa.Column("deduplication_key", sa.String(128), nullable=True))
    if "description" not in incident_columns:
        op.add_column("incidents", sa.Column("description", sa.Text(), nullable=True))
    if "metadata" not in event_columns:
        op.add_column("incident_events", sa.Column("metadata", sa.JSON(), nullable=True))
    index_names = {index["name"] for index in inspector.get_indexes("incidents")}
    if "ix_incidents_deduplication_key" not in index_names:
        op.create_index("ix_incidents_deduplication_key", "incidents", ["deduplication_key"])
    if "health_checks" not in inspector.get_table_names():
        op.create_table(
            "health_checks",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("service_id", sa.Integer(), sa.ForeignKey("services.id"), nullable=False),
            sa.Column("name", sa.String(120), nullable=False),
            sa.Column("check_type", sa.String(40), nullable=False),
            sa.Column("endpoint", sa.String(255), nullable=True),
            sa.Column("enabled", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    op.execute("UPDATE incidents SET deduplication_key = fingerprint, description = title")
    op.execute("UPDATE incident_events SET metadata = '{}' WHERE metadata IS NULL")
    with op.batch_alter_table("incidents") as batch:
        batch.alter_column("deduplication_key", nullable=False)
        batch.alter_column("description", nullable=False)
    with op.batch_alter_table("incident_events") as batch:
        batch.alter_column("metadata", nullable=False)


def downgrade():
    op.drop_table("health_checks")
    op.drop_index("ix_incidents_deduplication_key", table_name="incidents")
    op.drop_column("incident_events", "metadata")
    op.drop_column("incidents", "description")
    op.drop_column("incidents", "deduplication_key")
