@echo off
cd /d d:\code\codeByCursor\AI_EXAM\agri-qa-assistant\backend
echo Starting backend on 8001...
"C:\Users\FFY\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload