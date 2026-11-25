import sys, subprocess, time, json, collections
from playwright.sync_api import sync_playwright
import os
axe=open(os.environ.get('AXE_JS','node_modules/axe-core/axe.min.js')).read()
pages=sys.argv[2:]
srv=subprocess.Popen([sys.executable,"-m","http.server","8769","-d",sys.argv[1]],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
tot=collections.Counter(); ejemplos={}
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get("CHROME") or None,args=["--no-sandbox"])
    for pgname in pages:
        pg=b.new_page(color_scheme=("dark" if os.environ.get("MODO")=="oscuro" else "light")); pg.goto(f"http://localhost:8769/{pgname}"); pg.wait_for_timeout(12000)
        pg.add_script_tag(content=axe)
        r=pg.evaluate("async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}});return r.violations.map(v=>({id:v.id,impact:v.impact,n:v.nodes.length,help:v.help,ej:v.nodes.slice(0,2).map(n=>n.target.join(' ')+' :: '+(n.failureSummary||'').slice(0,160))}))}")
        for v in r:
            tot[(v['id'],v['impact'],v['help'])]+=v['n']; ejemplos.setdefault(v['id'],(pgname,v['ej']))
        pg.close()
    b.close()
srv.terminate()
for (i,imp,h),n in tot.most_common(): print(f"{n:4d} {imp:9s} {i} — {h}\n       ej: {ejemplos[i][0]} {ejemplos[i][1][:1]}")
print("Incidencias WCAG 2.1 AA:", sum(tot.values()))
sys.exit(1 if tot else 0)
