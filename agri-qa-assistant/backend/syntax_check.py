import py_compile, sys, io, traceback

f = r"d:\code\codeByCursor\AI_EXAM\agri-qa-assistant\backend\agent.py"
try:
    py_compile.compile(f, doraise=True)
    print("[OK] agent.py syntax")
except py_compile.PyCompileError as e:
    print(f"[SYNTAX ERROR]\n{e}")
    sys.exit(1)