from app.migrations.registry import SchemaMigration

MIGRATION = SchemaMigration(
    revision="0001_framework_baseline",
    down_revision=None,
    description="Record the framework schema baseline created by SQLAlchemy metadata.",
    upgrade=(),
    downgrade=(),
)
