# Quick test to find the startup error
import subprocess, sys

result = subprocess.run(
    [sys.executable, "-c", """
import sys
sys.path.insert(0, r'd:\\code\\codeByCursor\\AI_EXAM\\agri-qa-assistant\\backend')
try:
    from agent import agri_agent
    print('[OK] agent imported')
except Exception as e:
    print(f'[FAIL] agent import: {e}')
    import traceback; traceback.print_exc()

try:
    from tools import get_all_tools
    tools = get_all_tools()
    print(f'[OK] tools: {[t.name for t in tools]}')
except Exception as e:
    print(f'[FAIL] tools import: {e}')
    import traceback; traceback.print_exc()
"""],
    capture_output=True, text=True, cwd=r'd:\code\codeByCursor\AI_EXAM\agri-qa-assistant\backend'
)
print(result.stdout)
print(result.stderr)