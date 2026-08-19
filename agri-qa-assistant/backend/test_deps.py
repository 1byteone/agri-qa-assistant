import sys
sys.path.insert(0, r"d:\code\codeByCursor\AI_EXAM\agri-qa-assistant\backend")
try:
    import fastapi
    import langchain_openai
    import langchain_core
    import requests
    import bs4
    from tools import fetch_web_content
    from agent import AgricultureAgent
    print("ALL_DEPS_OK")
except ImportError as e:
    print(f"IMPORT_ERROR: {e}")