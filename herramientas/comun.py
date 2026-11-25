"""Utilidades comunes de las herramientas del libro.

Cada libro describe lo que lo distingue en libro.yml (slug, web, cita…) y en
_quarto.yml (título, autoría, DOI y capítulos). Las herramientas leen ambos.
"""
import pathlib, re, yaml

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def config():
    libro = yaml.safe_load((RAIZ / "libro.yml").read_text(encoding="utf-8"))
    quarto = yaml.safe_load((RAIZ / "_quarto.yml").read_text(encoding="utf-8"))
    libro["book"] = quarto["book"]
    libro.setdefault("web", f"https://pablosancheznunez.com/{libro['slug']}/")
    return libro


def capitulos(incluir_apendices=True):
    book = config()["book"]
    lista = []
    for c in book["chapters"]:
        lista += c["chapters"] if isinstance(c, dict) else [c]
    if incluir_apendices:
        lista += book.get("appendices", [])
    return lista


def cabecera(fichero):
    """Título y ancla (#sec-…) del primer encabezado de nivel 1 del capítulo."""
    for linea in (RAIZ / fichero).read_text(encoding="utf-8").splitlines():
        m = re.match(r"^# (.+?)\s*(\{#([^ }]+)[^}]*\})?\s*$", linea)
        if m:
            return m.group(1).strip(), m.group(3)
    return fichero, None


def version():
    cff = (RAIZ / "CITATION.cff").read_text(encoding="utf-8")
    m = re.search(r'^version:\s*"?([^"\n]+)"?', cff, flags=re.M)
    return m.group(1) if m else "1.0.0"
