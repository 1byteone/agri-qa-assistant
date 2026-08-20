import importlib.util, sys
for pkg in ["langchain", "chromadb", "langgraph", "openai"]:
    spec = importlib.util.find_spec(pkg)
    print(f"{pkg}: {'found' if spec else 'missing'}")