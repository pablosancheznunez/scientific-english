"""Resuelve en Chrome cada actividad interactiva (ordenar, clasificar, zonas,
escenario) y comprueba que el componente la da por buena; prueba también un
intento erróneo.   Uso: python3 interactivos.py CARPETA_BOOK pagina.html ..."""
import os, re, sys, subprocess, time
from playwright.sync_api import sync_playwright

raiz, paginas = sys.argv[1], sys.argv[2:]
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8767", "-d", raiz], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
FALLOS, total = [], 0
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get("CHROME") or None, args=["--no-sandbox"])
        for pag in paginas:
            pg = b.new_page(); errores = []
            pg.on("pageerror", lambda e: errores.append(str(e)))
            pg.goto(f"http://localhost:8767/{pag}"); pg.wait_for_timeout(1500)
            datos = pg.evaluate("window.IA_DATOS || {}")
            for id_, d in datos.items():
                total += 1
                caja = pg.locator(f"#{id_}")
                t = d["tipo"]
                caja.scroll_into_view_if_needed()
                if t == "ordenar":
                    caja.get_by_role("button", name=re.compile(r"^(Comprobar|Check)$")).click()
                    malo = caja.locator(".ia-aviso").inner_text()
                    n = len(d["items"])
                    for objetivo in range(n):
                        while True:
                            idxs = caja.locator(".ia-item").evaluate_all("els => els.map(e => +e.dataset.idx)")
                            k = idxs.index(objetivo)
                            if k == objetivo: break
                            caja.locator(".ia-item").nth(k).locator(".ia-mover").first.click()
                elif t == "clasificar":
                    filas = caja.locator(".ia-fila")
                    caja.get_by_role("button", name=re.compile(r"^(Comprobar|Check)$")).click()
                    malo = caja.locator(".ia-aviso").inner_text()
                    cats = caja.evaluate("""(c) => { const d = window.IA_DATOS[c.id]; const tmp = document.createElement('div');
                        const norm = h => { tmp.innerHTML = h; return tmp.textContent.replace(/\\s+/g, ' ').trim(); };
                        const pool = d.items.map(it => [norm(it.texto), it.categoria]);
                        return [...c.querySelectorAll('.ia-fila .ia-texto')].map(e => { const t = e.textContent.replace(/\\s+/g, ' ').trim();
                          const k = pool.findIndex(x => x[0] === t); return k >= 0 ? pool.splice(k, 1)[0][1] : null; }); }""")
                    for i in range(filas.count()):
                        filas.nth(i).locator("select").select_option(cats[i])
                elif t == "zonas":
                    zs = caja.locator(".ia-zona")
                    zs.nth([i for i, z in enumerate(d["zonas"]) if not z["correcta"]][0] if not all(z["correcta"] for z in d["zonas"]) else 0).click()
                    caja.get_by_role("button", name=re.compile(r"^(Comprobar|Check)$")).click()
                    malo = caja.locator(".ia-aviso").inner_text()
                    for i in range(zs.count()):
                        pulsado = zs.nth(i).get_attribute("aria-pressed") == "true"
                        if pulsado != d["zonas"][i]["correcta"]: zs.nth(i).click()
                elif t == "escenario":
                    # camino hasta un final «bien» (búsqueda en anchura)
                    from collections import deque
                    cola, previo = deque([d["inicio"]]), {d["inicio"]: None}
                    meta = None
                    while cola:
                        x = cola.popleft(); n_ = d["nodos"][x]
                        if n_["final"] and n_["valor"] == "bien": meta = x; break
                        for j, o in enumerate(n_["opciones"]):
                            if o["destino"] not in previo: previo[o["destino"]] = (x, j); cola.append(o["destino"])
                    camino = []
                    while meta and previo[meta]: camino.append(previo[meta]); meta = previo[meta][0]
                    malo = "-"
                    for paso, (nodo, j) in enumerate(reversed(camino)):
                        caja.locator(".ia-paso").nth(paso).locator(".ia-opciones button").nth(j).click()
                if t != "escenario":
                    caja.get_by_role("button", name=re.compile(r"^(Comprobar|Check)$")).click()
                hecho = caja.evaluate("e => e.classList.contains('ia-hecho')")
                aviso = caja.locator(".ia-aviso").inner_text()
                print(("  OK  " if hecho else "  FALLA ") + f"{pag} {id_} [{t}] intento erróneo: «{malo[:50]}» → «{aviso[:50]}»")
                if not hecho: FALLOS.append(id_)
            if errores: FALLOS.append(pag + " JS"); print("  JS:", errores)
            pg.close()
        b.close()
finally:
    srv.terminate()
print(f"Actividades: {total} · FALLOS: {len(FALLOS)} {FALLOS}")
