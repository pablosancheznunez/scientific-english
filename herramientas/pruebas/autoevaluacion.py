import sys, subprocess, time
import os
from playwright.sync_api import sync_playwright
root=sys.argv[1]; pages=sys.argv[2:]; FALLOS=[]
srv=subprocess.Popen([sys.executable,"-m","http.server","8766","-d",root],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get("CHROME") or None,args=["--no-sandbox"])
    for page in pages:
      pg=b.new_page(); errs=[]
      pg.on("pageerror", lambda e: errs.append(str(e)))
      pg.goto(f"http://localhost:8766/{page}"); pg.wait_for_timeout(3000)
      box=pg.locator(".webex-check").first
      # 1) cada select: elegir la correcta
      sels=box.locator("select.webex-select"); n=sels.count()
      for i in range(n): sels.nth(i).select_option("answer")
      # 2) radios: marcar la correcta
      rads=box.locator('input[type=radio][value=answer]')
      for i in range(rads.count()): rads.nth(i).check()
      # 3) fitb: escribir la primera respuesta
      ins=box.locator("input.webex-solveme")
      for i in range(ins.count()):
        import json
        ans=json.loads(ins.nth(i).get_attribute("data-answer"))[0]
        ins.nth(i).fill(ans); ins.nth(i).dispatch_event("keyup")
      box.locator("button.webex-check-button").click()
      total=box.locator(".webex-total_correct").inner_text()
      # respuesta incorrecta en el primer select
      wrong=None
      if n:
        opts=sels.nth(0).locator("option[value=x]")
        sels.nth(0).select_option(index=1 if sels.nth(0).locator("option").nth(1).get_attribute("value")=="x" else 2)
        wrong=sels.nth(0).get_attribute("class")
      sol=pg.locator(".webex-solution").first; sol.locator("button").click()
      abierta="open" in (sol.get_attribute("class") or "")
      import re as _re
      ok=_re.match(r"(\d+) (?:de|of) (\d+)", total)
      if not ok or ok.group(1)!=ok.group(2) or errs: FALLOS.append(page)
      print(f"{page}: selects={n} radios={rads.count()} huecos={ins.count()} | {total} | tras fallo: {wrong} | solución abierta={abierta} | errores JS={errs}")
      pg.close()
    b.close()
finally: srv.terminate()
print("Fallos:", FALLOS)
sys.exit(1 if FALLOS else 0)
