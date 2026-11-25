"""Genera un script .R limpio por capítulo (los que tienen código de R) a partir
de los bloques {webr} del .qmd, en plantillas/<capítulo>.R.

Uso, desde herramientas/ o la raíz:   python3 herramientas/extraer_r.py
"""
import re, sys
sys.path.insert(0, __import__("pathlib").Path(__file__).resolve().parent.as_posix())
from comun import RAIZ, cabecera, capitulos, config

cfg = config()
book = cfg["book"]
blk = re.compile(r"^```\{webr\}\n(.*?)^```", re.S | re.M)
head = re.compile(r"^(#{2,3}) (.+)$", re.M)
(RAIZ / "plantillas").mkdir(exist_ok=True)
for qmd in capitulos(incluir_apendices=False):
    txt = (RAIZ / qmd).read_text(encoding="utf-8")
    if "```{webr}" not in txt:
        continue
    titulo, _ = cabecera(qmd)
    titulo = re.sub(r"\s*\{[^}]*\}", "", titulo)
    out = [f"# {titulo}",
           f"# {book['title']}",
           f"# {book['author'][0]['name']} (UC3M) · https://doi.org/{book.get('doi', '')}",
           f"# Licencia del código: MIT · Libro: {cfg['web']}",
           "#",
           "# Script con todo el código del capítulo, para ejecutarlo en RStudio o Positron.",
           "# Los ejercicios tienen huecos (______): complétalos y compara con el libro.",
           ""]
    if cfg.get("paquete"):
        out += [f"# Funciones del paquete {cfg['paquete']} (instálalo una vez):",
                f"# remotes::install_github(\"{cfg['paquete_github']}\")",
                f"library({cfg['paquete']})", ""]
    ficheros = sorted(set(re.findall(r'"(datos/[^"]+\.(?:csv|json))"', txt)))
    if ficheros:
        out += ["# Descarga de los datos del capítulo a la carpeta datos/", 'dir.create("datos", showWarnings = FALSE)']
        for f in ficheros:
            out += [f'if (!file.exists("{f}")) download.file("{cfg["web"]}{f}", "{f}", mode = "wb")']
        out.append("")
    ultimo = None
    for m in blk.finditer(txt):
        hs = list(head.finditer(txt, 0, m.start()))
        if hs:
            t = re.sub(r"\s*\{[^}]*\}", "", hs[-1].group(2)).strip()
            if t != ultimo:
                out += ["", "# " + "-" * 70, f"# {t}", "# " + "-" * 70]
                ultimo = t
        body = m.group(1)
        o = " ".join(l for l in body.splitlines() if l.startswith("#|"))
        code = "\n".join(l for l in body.splitlines() if not l.startswith("#|")).strip("\n")
        code = re.sub(r'^source\("datos/[^"]+\.R"\)\n?', "", code, flags=re.M) if cfg.get("paquete") else code
        if "check: true" in o or not code.strip():
            continue
        if "setup: true" in o:
            out += ["# (preparación del ejercicio)", code, ""]
        elif "exercise:" in o:
            out += ["# EJERCICIO: completa los huecos ______", code, ""]
        else:
            out += [code, ""]
    nombre = qmd.replace(".qmd", "").replace("-", "_")
    (RAIZ / "plantillas" / f"{nombre}.R").write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    print(nombre)
