"""CORS contract tests that run entirely in-process via FastAPI TestClient."""
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app


_ORIGIN = "http://localhost:3000"


def test_chat_preflight_returns_cors_headers():
    with TestClient(app) as client:
        response = client.options(
            "/chat",
            headers={
                "Origin": _ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] in {"*", _ORIGIN}
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "content-type" in response.headers["access-control-allow-headers"].lower()


def test_chat_post_returns_cors_header_without_calling_external_llm():
    fake_result = {
        "thread_id": "cors-test",
        "message": "农业问题请提供作物和地区信息。",
        "sources": [],
        "tool_calls": [],
        "answer_mode": "professional",
        "completion_status": "complete",
    }
    with patch("main.agri_agent.chat", new=AsyncMock(return_value=fake_result)):
        with TestClient(app) as client:
            response = client.post(
                "/chat",
                headers={"Origin": _ORIGIN, "Content-Type": "application/json"},
                json={"message": "请写一首星空诗", "thread_id": "cors-test"},
            )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] in {"*", _ORIGIN}
    assert response.json()["thread_id"] == "cors-test"
