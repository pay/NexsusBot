import ast, json, os, re, sys, unicodedata
os.chdir('/data/data/com.termux/files/home/NexsusBot')
exps = ('access basic_control bot_sends config cron exp_control game get_iq help '
        'info lang note sconf_attrs sheriff talkers user_stats wtf').split()

def emoji_prefix(s):
    """Leading run of non-ASCII, non-letter symbol glyphs."""
    out = []
    for ch in s:
        if ord(ch) > 0x2100 and not ch.isalpha():
            out.append(ch)
        else:
            break
    return ''.join(out)

def edge(s):
    """Leading/trailing whitespace signature: newlines before/after content."""
    m = re.match(r'^[ \t\n\r]*', s).group(0)
    t = re.search(r'[ \t\n\r]*$', s).group(0)
    return (m.count('\n'), t.count('\n'), m.count('\t'), t.count('\t'))

bad = 0
for exp in exps:
    d = None
    for n in ast.walk(ast.parse(open('expansions/%s/code.py' % exp, encoding='utf-8').read())):
        if isinstance(n, ast.Assign) and getattr(n.targets[0], 'id', '') == 'AnsBase':
            d = ast.literal_eval(n.value); break
    raw = open('expansions/%s/ans.fr.json' % exp, encoding='utf-8').read()
    if '\\u' in raw:
        print('UNICODE-ESCAPE', exp); bad += 1
    loc = json.load(open('expansions/%s/ans.fr.json' % exp, encoding='utf-8'))
    for k, v in sorted(loc.items(), key=lambda x: int(x[0])):
        i = int(k); en = d[i]
        if emoji_prefix(en) != emoji_prefix(v):
            print('EMOJI', exp, i, repr(emoji_prefix(en)), repr(emoji_prefix(v))); bad += 1
        if edge(en) != edge(v):
            print('EDGE-WS', exp, i, edge(en), edge(v)); bad += 1
        # newline count parity (fragments are concatenated)
        if en.count('\n') != v.count('\n'):
            print('NL-COUNT', exp, i, en.count('\n'), v.count('\n')); bad += 1
        # angle-bracket literal tokens must be identical
        if re.findall(r'<[^>]+>', en) != re.findall(r'<[^>]+>', v):
            print('ANGLE-TOKEN', exp, i); bad += 1
        if v != v.strip('\n') and en.strip('\n') == en:
            print('UNEXPECTED-EDGE-NL', exp, i); bad += 1
    # no extra keys beyond English non-empty set
    want = {str(i) for i, x in enumerate(d) if x and x.strip()}
    if set(loc) != want:
        print('KEYSET', exp, sorted(set(loc) ^ want, key=int)); bad += 1

print('strict problems:', bad)
sys.exit(1 if bad else 0)
