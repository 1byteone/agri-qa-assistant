data = open(r'd:\code\codeByCursor\AI_EXAM\agri-qa-assistant\backend\agent.py', 'rb').read()
lines = data.split(b'\n')
for i, l in enumerate(lines[88:96], 89):
    print(f'{i}: {repr(l)}')