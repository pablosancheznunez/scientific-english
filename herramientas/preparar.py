"""Genera los ficheros que dependen de la configuración del libro:

- sw.js: service worker para el uso sin conexión (versión y páginas del libro).
- .github/workflows/comprobar.yml: integración continua con las páginas reales.

Uso, desde la raíz del libro:   python3 herramientas/preparar.py
"""
import json
from comun import RAIZ, capitulos, config, version

cfg = config()
paginas = [""] + [c.replace(".qmd", ".html") for c in capitulos()] + ["search.json"]

sw = (RAIZ / "herramientas" / "sw.plantilla.js").read_text(encoding="utf-8")
sw = sw.replace("__VERSION__", version()).replace("__SLUG__", cfg["slug"])
sw = sw.replace("__PAGINAS__", json.dumps(paginas, ensure_ascii=False))
(RAIZ / "sw.js").write_text(sw, encoding="utf-8")

con_r = [c for c in capitulos() if "```{webr}" in (RAIZ / c).read_text(encoding="utf-8") and "#| exercise:" in (RAIZ / c).read_text(encoding="utf-8")]
html = [c.replace(".qmd", ".html") for c in capitulos()]
ci = (RAIZ / "herramientas" / "comprobar.plantilla.yml").read_text(encoding="utf-8")
ci = ci.replace("__EJERCICIOS__", " ".join(con_r) or "index.qmd")
ci = ci.replace("__PAGINAS__", " ".join(html))
(RAIZ / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
(RAIZ / ".github" / "workflows" / "comprobar.yml").write_text(ci, encoding="utf-8")
print("sw.js y comprobar.yml para", cfg["slug"], version(), "·", len(paginas), "páginas")
