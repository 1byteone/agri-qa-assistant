import sys
sys.path.insert(0, r'd:\code\codeByCursor\AI_EXAM\agri-qa-assistant\backend')

import config
print(f"config file: {config.__file__}")

from config import settings
print(f"agnes_base_url: {settings.agnes_base_url}")
print(f"agnes_chat_model: {settings.agnes_chat_model}")
print(f"agnes_api_key prefix: {settings.agnes_api_key[:12]}...")
print(f"http_proxy: {settings.http_proxy}")
print(f"https_proxy: {settings.https_proxy}")