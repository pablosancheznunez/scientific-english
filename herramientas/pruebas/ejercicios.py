"""Abre cada capítulo en Chrome headless, espera a webR, revisa las celdas autorun
y resuelve cada ejercicio con su solución, leyendo la retroalimentación."""
import os, re, sys, subprocess, time, pathlib
from playwright.sync_api import sync_playwright

LIBRO = pathlib.Path(sys.argv[1])
espera = int(sys.argv[2])
paginas = sys.argv[3:]

def soluciones(qmd):
    txt = (LIBRO / qmd).read_text()
    return {m.group(1): m.group(2) for m in re.finditer(
        r'::: \{\.solution exercise="([^"]+)"\}\s*\n```(?:r|python)\n(.*?)```', txt, re.S)}

JS_LOCALIZA = """(ej) => {
  for (const s of document.querySelectorAll('script[type^="webr-"][type$="-contents"], script[type^="pyodide-"][type$="-contents"]')) {
    const d = JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(s.textContent.trim()), c => c.charCodeAt(0))));
    if (d.attr.exercise === ej && !d.attr.setup && !d.attr.check) return s.type.replace('-contents','');
  }
  return null;
}"""

JS_FIJA = """([id, codigo]) => {
  const cell = document.getElementById(id);
  const cm = cell.querySelector('.cm-content');
  const view = cm.cmView.view ?? cm.cmView.rootView.view;
  view.dispatch({changes: {from: 0, to: view.state.doc.length, insert: codigo}});
  return true;
}"""

srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "-d", str(LIBRO / "_book")],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
fallos = 0
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get("CHROME") or None, args=["--no-sandbox"])
        for qmd in paginas:
            html = qmd.replace(".qmd", ".html")
            pg = b.new_page(viewport={"width": 1300, "height": 900})
            externas = []
            pg.route(re.compile(r"https?://(?!localhost).*"), lambda r: (externas.append(r.request.url), r.abort()) if ("r-wasm.org" in r.request.url or "jsdelivr" in r.request.url or "pypi" in r.request.url) else r.continue_())
            errores = []
            pg.on("pageerror", lambda e: errores.append(str(e)))
            pg.goto(f"http://localhost:8765/{html}", wait_until="load")
            pg.wait_for_timeout(espera * 1000)
            salidas = pg.eval_on_selector_all(".cell-output-container", "els => els.map(e => e.innerText)")
            vacias = sum(1 for s in salidas if not s.strip())
            errs_r = [s[:250] for s in salidas if re.search(r"Error|Warning|Aviso", s)]
            print(f"\n=== {html}: bloqueadas CDN: {len(externas)}");print(f"=== {html}: {len(salidas)} contenedores ({vacias} vacíos); errores/avisos en autorun: {len(errs_r)}; JS: {errores[:3]}")
            for e in errs_r: print("   R>", e.replace("\n", " | "))
            for ej, codigo in soluciones(qmd).items():
                cid = pg.evaluate(JS_LOCALIZA, ej)
                if not cid:
                    print(f"  [{ej}] no encontrado"); fallos += 1; continue
                pg.evaluate(JS_FIJA, [cid, codigo])
                cell = pg.locator(f"#{cid}")
                cell.get_by_role("button", name=re.compile("Run Code")).click()
                pg.wait_for_timeout(6000)
                texto = cell.inner_text()
                fb = re.findall(r"(Correct[^\n]*|Todav[^\n]*|Revis[^\n]*|Incorrect[^\n]*|Error[^\n]*)", texto)
                estado = "OK " if any(f.startswith("Correct") for f in fb) else "MAL"
                if estado == "MAL": fallos += 1
                print(f"  {estado} [{ej}] {' / '.join(fb)[:200] or texto[-300:].replace(chr(10),' | ')}")
            pg.screenshot(path=f"/home/claude/tools/cap_{html}.png", full_page=True)
            pg.close()
        b.close()
finally:
    srv.terminate()
print("\nFALLOS:", fallos)
sys.exit(1 if fallos else 0)
