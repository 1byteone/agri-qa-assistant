"""Transport contract test for the POST SSE endpoint without an external LLM."""
import asyncio
import json

from agent import agri_agent
from main import chat_stream
from schemas import ChatRequest


async def fake_stream_chat(**_kwargs):
    yield {"type": "status", "message": "正在检索"}
    yield {"type": "delta", "text": "水稻"}
    yield {"type": "ui", "component": "knowledge-context", "props": {"items": []}}
    yield {"type": "done", "thread_id": "stream-test", "message": "水稻", "tool_calls": []}


async def run_contract_test():
    original_stream_chat = agri_agent.stream_chat
    agri_agent.stream_chat = fake_stream_chat
    try:
        response = await chat_stream(ChatRequest(message="测试", thread_id="stream-test"))
        assert response.media_type == "text/event-stream"
        frames = []
        async for chunk in response.body_iterator:
            frames.extend([frame for frame in chunk.split("\n\n") if frame])

        assert [frame.split("\n", 1)[0] for frame in frames] == [
            "event: status",
            "event: delta",
            "event: ui",
            "event: done",
        ]
        payloads = [json.loads(frame.split("data: ", 1)[1]) for frame in frames]
        assert payloads[1] == {"type": "delta", "text": "水稻"}
        assert payloads[-1]["thread_id"] == "stream-test"
    finally:
        agri_agent.stream_chat = original_stream_chat


async def run_guard_contract_test():
    """The real agent must short-circuit an out-of-scope prompt."""
    events = []
    async for event in agri_agent.stream_chat("99乘法表java实现", "guard-test"):
        events.append(event)
    assert [event["type"] for event in events] == ["guard", "delta", "done"]
    assert events[0]["guarded"] is True
    assert events[-1]["tool_calls"] == []
    assert events[-1]["guarded"] is True


if __name__ == "__main__":
    asyncio.run(run_contract_test())
    asyncio.run(run_guard_contract_test())
    print("stream contract passed")
