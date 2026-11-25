"""Genera diapositivas de clase (reveal.js) a partir de los capítulos: el
título, los objetivos, las figuras con su pie, las tablas principales y las
preguntas de autoevaluación como preguntas para el aula. Salen en
_book/diapositivas/<capitulo>.html, cada una en un solo fichero.

Uso, desde la raíz del libro, después de `quarto render`:
    python3 herramientas/diapositivas.py
"""
import pathlib, re, shutil, subprocess, sys, yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from comun import config, capitulos  # noqa: E402

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CFG = config()
TMP = RAIZ / "_diapositivas"
SALIDA = RAIZ / "_book" / "diapositivas"
EN = CFG.get("idioma") == "en"


def tr(es, en):
    return en if EN else es


def limpiar_md(t):
    t = re.sub(r"\{\{< (mcq|longmcq) (.*?) >\}\}", lambda m: " / ".join(x.strip('"*') for x in re.findall(r'"[^"]*"', m.group(2))), t)
    t = re.sub(r"\{\{< torf (true|false) >\}\}", tr("(¿verdadero o falso?)", "(true or false?)"), t)
    t = re.sub(r"\{\{< fitb .*? >\}\}", "______", t)
    t = re.sub(r"\]\(9\d-glosario\.qmd#[^)]+\)", "]()", t).replace("[]()", "")
    t = re.sub(r"\[([^\]]+)\]\(\)", r"\1", t)
    return t


def bloques_div(texto, clase):
    m = re.search(r"::: \{[^}]*\." + re.escape(clase) + r"[^}]*\}\n(.*?)\n:::\n", texto, re.S)
    return m.group(1) if m else ""


def tablas(texto, maximo=3):
    salida = []
    for sec in re.split(r"\n(?=## )", texto):
        cab = sec.split("\n", 1)[0]
        if re.match(r"## (Lectura|Autoevaluación|Recursos|Reto|Descargas|Glosario|Laboratorio|Actividades|Required reading|Self-assessment|Resources|Challenge|Downloads|Glossary|Lab|Activities|Further reading)", cab):
            continue
        for t in re.findall(r"((?:^\|.*\|\n)+)", sec, re.M):
            filas = t.strip().split("\n")
            if 3 <= len(filas) <= 9:
                salida.append((re.sub(r"^#+\s*\d*\.?\s*", "", cab).strip(), t.strip()))
    return salida[:maximo]


def diapositivas(fichero):
    txt = (RAIZ / fichero).read_text()
    txt = txt.split("---", 2)[2] if txt.startswith("---") else txt
    titulo = re.search(r"^# (.+?)(\s*\{.*\})?$", txt, re.M).group(1).strip()
    partes = [f"## {titulo}\n\n{CFG['titulo_portada']}\n\n{CFG['web']}{fichero.replace('.qmd', '.html')}\n"]
    obj = re.search(r"## (?:Objetivos|Objectives)\n(.*?)\n:::", txt, re.S)
    if obj:
        partes.append(tr("## Objetivos", "## Objectives") + "\n\n" + obj.group(1).strip() + "\n")
    for cap, ruta, _ in re.findall(r"!\[(.+?)\]\((figuras/[^)]+)\)(\{[^}]*\})?", txt):
        alt = re.search(r'fig-alt="([^"]*)"', _ or "")
        corto = cap.split(". ")[0].rstrip(".")
        partes.append(f"## {corto}\n\n![]({ruta}){{fig-alt=\"{alt.group(1) if alt else cap}\" width=\"100%\"}}\n\n::: {{.notes}}\n{cap}\n:::\n")
    for cab, t in tablas(txt):
        partes.append(f"## {cab}\n\n{t}\n")
    lect = re.search(r"## (?:Lectura obligatoria|Required reading)\n\n::: \{\.lectura\}\n(.*?)\n:::", txt, re.S)
    if lect:
        partes.append(tr("## Lectura obligatoria", "## Required reading") + "\n\n" + lect.group(1).strip() + "\n")
    auto = bloques_div(txt, "webex-check")
    if auto:
        preguntas = [limpiar_md(p.strip()) for p in re.findall(r"^\d+\.\s+(.*)$", auto, re.M)]
        for i in range(0, len(preguntas), 4):
            partes.append(tr("## Para debatir", "## For discussion") + "\n\n" + "\n".join(f"{i + k + 1}. {p}" for k, p in enumerate(preguntas[i:i + 4])) + "\n")
    reto = re.search(r"## ((?:Reto de|Challenge for) [^\n]+)\n(.*?)\n\*\*(?:Entrega|Submission)", txt, re.S)
    if reto:
        partes.append(f"## {reto.group(1)}\n\n{reto.group(2).strip()}\n")
    cabecera = {"title": titulo, "author": "Pablo Sánchez-Núñez", "lang": tr("es", "en"),
                "format": {"revealjs": {"slide-number": True, "html-math-method": "plain", "embed-resources": False,
                                        "transition": "none", "width": 1280, "height": 720, "margin": 0.08,
                                        "footer": CFG["titulo_portada"], "css": "diapositivas.css"}}}
    return "---\n" + yaml.safe_dump(cabecera, allow_unicode=True, sort_keys=False) + "---\n\n" + "\n\n".join(partes)


def main():
    if TMP.exists():
        shutil.rmtree(TMP)
    if SALIDA.exists():
        shutil.rmtree(SALIDA)
    TMP.mkdir()
    (TMP / "_quarto.yml").write_text("project:\n  type: default\n")
    (TMP / "diapositivas.css").write_text(
        ".reveal { font-family: system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; }\n"
        ".reveal h2 { font-size: 1.4em; color: #000e78; }\n.reveal table { font-size: .6em; }\n"
        ".reveal .slide-number, .reveal .footer { color: #333; }\n")
    if (RAIZ / "figuras").exists():
        shutil.copytree(RAIZ / "figuras", TMP / "figuras")
    SALIDA.mkdir(parents=True, exist_ok=True)
    hechas = []
    for f in capitulos(incluir_apendices=False):
        if f in ("index.qmd",) or f.startswith("00"):
            continue
        destino = TMP / f
        destino.write_text(diapositivas(f))
        r = subprocess.run(["quarto", "render", str(destino), "--quiet"], cwd=TMP, capture_output=True, text=True)
        html = destino.with_suffix(".html")
        if r.returncode != 0 or not html.exists():
            print("ERROR", f, r.stderr[-500:])
            continue
        shutil.copy2(html, SALIDA / html.name)
        libs = TMP / (html.stem + "_files")
        if libs.exists():
            if (SALIDA / "libs").exists() is False:
                shutil.copytree(libs, SALIDA / "libs")
            texto = (SALIDA / html.name).read_text().replace(html.stem + "_files/", "libs/")
            (SALIDA / html.name).write_text(texto)
        shutil.copy2(TMP / "diapositivas.css", SALIDA / "diapositivas.css")
        if (TMP / "figuras").exists() and not (SALIDA / "figuras").exists():
            shutil.copytree(TMP / "figuras", SALIDA / "figuras")
        hechas.append(html.name)
    indice = [f"<!DOCTYPE html><html lang='{tr('es', 'en')}'><meta charset='utf-8'><title>{tr('Diapositivas', 'Slides')}</title>",
              "<body style='font-family:system-ui;max-width:40rem;margin:2rem auto'>",
              f"<h1>{tr('Diapositivas', 'Slides')}: {CFG['titulo_portada']}</h1><ul>"]
    indice += [f"<li><a href='{h}'>{h.replace('.html', '')}</a></li>" for h in hechas]
    indice.append(tr("</ul><p>Pulsa F para pantalla completa y S para ver las notas.</p></body></html>", "</ul><p>Press F for full screen and S for speaker notes.</p></body></html>"))
    (SALIDA / "index.html").write_text("\n".join(indice))
    shutil.rmtree(TMP)
    print(f"Diapositivas: {len(hechas)} -> {SALIDA}")


if __name__ == "__main__":
    main()
