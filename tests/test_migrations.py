
from pathlib import Path

def test_migration_file_exists():
    migration_dir = Path("migrations/versions")
    files = list(migration_dir.glob("*.py"))
    assert files, "No Alembic migration files found"


def test_initial_migration_contains_constraints():
    migration_file = Path("migrations/versions/001_initial_schema.py")
    content = migration_file.read_text(encoding="utf-8")

    assert "create_table" in content
    assert "UniqueConstraint" in content or "unique=True" in content
    assert "ForeignKey" in content
