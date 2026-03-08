import pytest
from app import create_app, db

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()

def test_index_loads(client):
    """Homepage returns 200"""
    response = client.get("/")
    assert response.status_code == 200  # ✅ FIXED

def test_add_task(client):
    response = client.post("/add", data={"title": "Test Task", "priority": "high"})
    assert response.status_code == 302

def test_stats_loads(client):
    response = client.get("/stats")
    assert response.status_code == 200

def test_tags_loads(client):
    response = client.get("/tags")
    assert response.status_code == 200

def test_search_loads(client):
    response = client.get("/search?q=test")
    assert response.status_code == 200
