import ast, os
os.chdir('/data/data/com.termux/files/home/NexsusBot')
d = None
for n in ast.walk(ast.parse(open('expansions/basic_control/code.py', encoding='utf-8').read())):
    if isinstance(n, ast.Assign) and getattr(n.targets[0], 'id', '') == 'AnsBase':
        d = ast.literal_eval(n.value); break
import json
loc = json.load(open('expansions/basic_control/ans.fr.json', encoding='utf-8'))
for i in (2, 3, 4):
    en, fr = d[i], loc[str(i)]
    print(i, 'EN', [hex(ord(c)) for c in en[:2]], repr(en))
    print(i, 'FR', [hex(ord(c)) for c in fr[:2]], repr(fr))
