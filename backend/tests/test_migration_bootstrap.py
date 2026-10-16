from app.migrate import BASELINE_SCHEMAS, LEGACY_PARTIAL_SCHEMAS, classify_schema


def test_known_migration_boundaries_are_classified_exactly():
    for revision, schema in BASELINE_SCHEMAS.items():
        assert classify_schema(schema) == revision


def test_unknown_or_partial_schema_is_rejected():
    schema = {"services": BASELINE_SCHEMAS["0001_initial"]["services"]}
    assert classify_schema(schema) is None


def test_known_legacy_partial_schema_is_classified_for_reconciliation():
    schema = LEGACY_PARTIAL_SCHEMAS["legacy_0001_plus_health_checks"]
    assert classify_schema(schema) == "legacy_0001_plus_health_checks"


def test_unknown_extra_column_is_not_stamped():
    schema = {table: set(columns) for table, columns in BASELINE_SCHEMAS["0005_incident_assignment"].items()}
    schema["services"].add("unreviewed_column")
    assert classify_schema(schema) is None
