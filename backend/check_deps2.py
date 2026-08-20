import sys
print("Python:", sys.executable)

deps = [
    ("fastapi", "FastAPI"),
    ("uvicorn", "Uvicorn"),
    ("langchain", "LangChain"),
    ("langchain_openai", "LangChain OpenAI"),
    ("langchain_community", "LangChain Community"),
    ("langgraph", "LangGraph"),
    ("chromadb", "ChromaDB"),
    ("pydantic", "Pydantic"),
    ("pydantic_settings", "Pydantic Settings"),
    ("sqlalchemy", "SQLAlchemy"),
    ("aiosqlite", "aiosqlite"),
]

missing = []
for mod, name in deps:
    try:
        __import__(mod)
        print(f"[OK] {name}")
    except Exception as e:
        print(f"[FAIL] {name}: {e}")
        missing.append(name)

if missing:
    print("\nMissing:", missing)
else:
    print("\nAll dependencies OK")