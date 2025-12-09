import os
import subprocess
import tempfile
from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_creates_tables(tmp_path):
    db_file = tmp_path / 'alembic_test.db'
    db_url = f"sqlite:///{db_file}"
    env = os.environ.copy()
    env['DATABASE_URL'] = db_url
    # Run alembic upgrade head
    subprocess.check_call(['alembic', 'upgrade', 'head'], env=env)

    # Verify tables exist
    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert 'clients' in tables
    assert 'masters' in tables
    assert 'services' in tables
    assert 'bookings' in tables
    assert 'admin_audit_log' in tables
    assert 'inka_training' in tables
