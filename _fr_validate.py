import ast, json, re, sys
os_path = '/data/data/com.termux/files/home/NexsusBot'
import os
os.chdir(os_path)
def specs(s): return sorted(re.findall(r'%[-0-9.]*[a-z]', s))
bad=0; exps='access basic_control bot_sends config cron exp_control game get_iq help info lang note sconf_attrs sheriff talkers user_stats wtf'.split()
for exp in exps:
    p='expansions/%s/ans.fr.json'%exp; cf='expansions/%s/code.py'%exp
    d=None
    for n in ast.walk(ast.parse(open(cf,encoding='utf-8').read())):
        if isinstance(n,ast.Assign) and getattr(n.targets[0],'id','')=='AnsBase': d=ast.literal_eval(n.value); break
    loc=json.load(open(p,encoding='utf-8'))
    for k,v in loc.items():
        k=int(k)
        if not (0<=k<len(d)): print('RANGE',exp,k); bad+=1
        elif specs(d[k])!=specs(v): print('SPEC',exp,k,specs(d[k]),specs(v)); bad+=1
        elif '\\n' in v: print('LIT-N',exp,k); bad+=1
    miss=[i for i,x in enumerate(d) if x and x.strip() and str(i) not in loc]
    if miss: print('MISSING',exp,miss); bad+=1
print('problems:',bad); sys.exit(1 if bad else 0)
