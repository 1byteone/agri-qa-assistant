from pathlib import Path

from fastapi.testclient import TestClient

from phase4_mini_rag_system.app import create_app


def test_end_to_end_search_and_chat(tmp_path: Path) -> None:
    (tmp_path / "guide.md").write_text(
        "# Guide\n\nChunk overlap 可以保留跨边界上下文。\n",
        encoding="utf-8",
    )
    client = TestClient(create_app(tmp_path))

    health = client.get("/health")
    index = client.get("/")
    search = client.post("/search", json={"query": "overlap 上下文", "top_k": 3})
    chat = client.post("/chat", json={"query": "overlap 上下文", "top_k": 3})

    assert health.status_code == 200
    assert index.status_code == 200
    assert health.json()["chunks"] > 0
    assert search.status_code == 200
    assert search.json()["results"][0]["source"].endswith("guide.md")
    assert chat.json()["mode"] == "evidence-only"
    assert chat.json()["citations"]


def test_search_rejects_empty_query(tmp_path: Path) -> None:
    (tmp_path / "guide.md").write_text("内容", encoding="utf-8")
    client = TestClient(create_app(tmp_path))

    response = client.post("/search", json={"query": ""})

    assert response.status_code == 422
