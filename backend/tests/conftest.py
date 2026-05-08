import os
import pytest

# Force in-memory database for all tests to prevent Postgres connection errors
# and global state pollution across tests.
os.environ["USE_MEMORY_DB"] = "true"

# Import main immediately to force sys.modules["database"] patching
# before any other test file imports router.py or admin_router.py
import sys
import pathlib

# Add backend dir to sys.path so 'main' can be imported
backend_dir = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import main

@pytest.fixture(autouse=True)
def clear_memory_db():
    """Clear the in-memory database before every test."""
    try:
        import database_memory as _db
        _db._sessions.clear()
        _db._global_states.clear()
        _db._bu_states.clear()
        _db._decision_log.clear()
    except ImportError:
        pass
