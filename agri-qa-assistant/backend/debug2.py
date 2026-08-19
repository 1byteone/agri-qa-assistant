import sys
f = r'd:\code\codeByCursor\AI_EXAM\agri-qa-assistant\backend\agent.py'
data = open(f, 'rb').read()
lines = data.split(b'\n')
for i, l in enumerate(lines[88:96], 89):
    print(f'{i}: {repr(l)}')
    if i == 92:
        # Check what char 92 is
        print(f'  -> hex at that position')
sys.exit(0)