import pytest

from app import create_app, store


@pytest.fixture
def client(tmp_path): # tmp_path provides a temporary directory for current test's files
    app = create_app()
    app.config["TESTING"] = True
    app.config["BACKUP_FILE"] = str(tmp_path / "backup.json")  # Backup writes go to temporary file
    store.reset()
    with app.test_client() as client:
        yield client
    store.reset()
