"""End-to-end stream orchestration test with a deterministic local model stub."""
import asyncio

from langchain_core.messages import AIMessage

from agent import agri_agent
from knowledge_base import knowledge_base
from memory import conversation_memory


class _LocalModel:
    async def astream(self, _messages):
        yield AIMessage(content="现场摘要\n水稻叶片发黄，待补充地区和生育期。\n\n优先判断\n信息不足，先排查病虫害和缺素。\n\n现在做什么\n记录扩散范围并补充照片。\n\n风险边界\n农药按登记标签使用。\n\n复查节点\n24-48小时后复查。")


async def _empty_history(*_args, **_kwargs):
    return []


async def _empty_memories(*_args, **_kwargs):
    return {"used": [], "skipped": []}


async def _not_organized(*_args, **_kwargs):
    return {"triggered": False, "conflicts": [], "archived": 0}


async def _noop(*_args, **_kwargs):
    return None


async def run_contract_test():
    original = {
        "llm": agri_agent.llm,
        "search": knowledge_base.search,
        "history": conversation_memory.get_history,
        "memories": conversation_memory.relevant_memories,
        "organize": conversation_memory.organize_if_needed,
        "add": conversation_memory.add_message,
    }
    agri_agent.llm = _LocalModel()
    knowledge_base.search = lambda *_args, **_kwargs: []
    conversation_memory.get_history = _empty_history
    conversation_memory.relevant_memories = _empty_memories
    conversation_memory.organize_if_needed = _not_organized
    conversation_memory.add_message = _noop
    try:
        events = [event async for event in agri_agent.stream_chat("水稻叶片发黄怎么防治？", "memory-stream-contract")]
        event_types = [event["type"] for event in events]
        assert "memory-action" in event_types
        assert event_types[-1] == "done"
        assert events[-1]["message"]
    finally:
        agri_agent.llm = original["llm"]
        knowledge_base.search = original["search"]
        conversation_memory.get_history = original["history"]
        conversation_memory.relevant_memories = original["memories"]
        conversation_memory.organize_if_needed = original["organize"]
        conversation_memory.add_message = original["add"]


def test_memory_stream_contract():
    asyncio.run(run_contract_test())


if __name__ == "__main__":
    asyncio.run(run_contract_test())
    print("memory stream contract passed")
