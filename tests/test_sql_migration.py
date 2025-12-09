from src.db.sql_client import SQLClient


def test_create_tables_memory():
    # Use SQLite in-memory to ensure tables can be created
    db = SQLClient(database_url='sqlite+pysqlite:///:memory:')
    db.create_tables()
    # If no exception is raised, success
    assert True
