import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_agent_stream_success():
    response = client.get("/api/agent/stream")

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    body = response.text

    assert "event: message" in body
    assert "event: done" in body
    assert "final_decision" in body


def test_agent_stream_not_found():
    response = client.get("/api/wrong-url")

    assert response.status_code == 404