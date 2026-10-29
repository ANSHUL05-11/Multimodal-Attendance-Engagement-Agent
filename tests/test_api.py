"""Tests for FastAPI backend REST endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from database.database import Base, engine, init_db


@pytest.fixture(scope="module", autouse=True)
def setup_api_database():
    """Ensure database schema is ready before API testing."""
    init_db()


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "environment" in data
    assert "opencv_version" in data["environment"]


def test_session_api_crud(client):
    # 1. Create session
    payload = {"title": "API Test Class", "course_code": "CS101", "instructor_name": "Prof. Turing"}
    res = client.post("/api/sessions", json=payload)
    assert res.status_code == 201
    s = res.json()
    assert s["title"] == "API Test Class"
    session_id = s["id"]

    # 2. Get session
    res_get = client.get(f"/api/sessions/{session_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == session_id

    # 3. List sessions
    res_list = client.get("/api/sessions")
    assert res_list.status_code == 200
    assert any(item["id"] == session_id for item in res_list.json())

    # 4. Get 404 for non-existent session
    res_404 = client.get("/api/sessions/999999")
    assert res_404.status_code == 404


def test_participant_api_crud(client):
    payload = {"student_id": "API-STU-99", "name": "Ada Lovelace", "department": "Computer Science"}
    res = client.post("/api/participants", json=payload)
    assert res.status_code in [201, 400]  # 400 if already created in rerun

    res_list = client.get("/api/participants")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1


def test_session_export_endpoint(client):
    # Create test session
    payload = {"title": "Export Test", "course_code": "CS200"}
    res = client.post("/api/sessions", json=payload)
    s_id = res.json()["id"]

    res_exp = client.get(f"/api/sessions/{s_id}/export?export_type=attendance")
    assert res_exp.status_code == 200
    assert "track_id" in res_exp.text
