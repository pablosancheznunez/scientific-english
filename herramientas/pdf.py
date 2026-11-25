"""Genera las versiones PDF (con Typst) y EPUB del libro.

Quarto no admite Typst en proyectos de libro, así que este script une los
capítulos en un solo documento dentro de _pdf/ (un proyecto aparte), lo
compila y deja el resultado en pdf/<slug>.pdf y pdf/<slug>.epub.

Uso, desde la raíz del libro:   python3 herramientas/pdf.py
Después, `quarto render` copia la carpeta pdf/ al sitio.
"""
import pathlib, re, shutil, subprocess, sys, yaml
sys.path.insert(0, pathlib.Path(__file__).resolve().parent.as_posix())
from comun import cabecera as cabecera_cap, capitulos as lista_capitulos, config

RAIZ = pathlib.Path(__file__).resolve().parent.parent
BUILD = RAIZ / "_pdf"
CFG = config()
SLUG = CFG["slug"]
WEB = CFG["web"]
SALIDA = RAIZ / "pdf" / f"{SLUG}.pdf"

cfg = yaml.safe_load((RAIZ / "_quarto.yml").read_text())
libro = cfg["book"]
capitulos = lista_capitulos()

def cuerpo(fichero):
    s = (RAIZ / fichero).read_text()
    if s.startswith("---"):
        s = s.split("---", 2)[2]
    return s.strip() + "\n"

autor0 = yaml.safe_load((RAIZ / "_quarto.yml").read_text())["book"]["author"][0]
doi0 = yaml.safe_load((RAIZ / "_quarto.yml").read_text())["book"].get("doi")
linea_doi = f"- **DOI:** [https://doi.org/{doi0}](https://doi.org/{doi0})\n" if doi0 else ""
cita_doi = f" <https://doi.org/{doi0}>" if doi0 and doi0 not in CFG["cita"] else ""
EN = CFG.get("idioma") == "en"
def tr(es, en): return en if EN else es
ficha = f"""
::: {{.callout-note title="{tr('Ficha del libro', 'About this book')}"}}
- **{tr("Autor", "Author")}:** {autor0["name"]}
- **ORCID:** [https://orcid.org/{autor0["orcid"]}](https://orcid.org/{autor0["orcid"]})
- **{"Author website" if CFG.get("idioma") == "en" else "Web del autor"}:** [https://pablosancheznunez.com](https://pablosancheznunez.com)
- **{tr("Afiliación", "Affiliation")}:** {autor0["affiliation"]}
{linea_doi}- **{tr("Licencia", "Licence")}:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/{tr("deed.es", "")})
- **{tr("Versión web interactiva", "Interactive web version")}:** <{WEB}>
- **{tr("Cómo citarlo", "How to cite")}:** {CFG["cita"]}{cita_doi}
:::
"""

aviso = f"""
::: {{.callout-note title="{tr('Sobre esta versión en PDF', 'About this PDF version')}"}}
{tr("Esta es la versión para leer e imprimir. El código aparece sin ejecutar, las preguntas de autoevaluación se muestran sin corrección automática y las actividades interactivas aparecen en papel, con su solución; los laboratorios solo funcionan en la web. Para ejecutar el código, hacer los ejercicios con corrección y responder a las preguntas, usa la versión web", "This is the version for reading and printing. Self-assessment questions are shown without automatic marking and the interactive activities appear on paper with their solutions; the labs only work on the web. To do the exercises with feedback and answer the questions, use the web version")}: <{WEB}>.
:::

"""

partes = []
for i, f in enumerate(capitulos):
    txt = cuerpo(f)
    if f == "index.qmd":
        # tras el encabezado de la presentación, el aviso
        txt = re.sub(r"(# (?:Presentación|Preface|Welcome)[^\n]*\n)", lambda m: m.group(1) + ficha + aviso, txt, count=1)
        # el botón de descarga del CSV y la celda de prueba no tienen sentido en papel
        txt = re.sub(r"\[Descargar el CSV\][^\n]*\n", "", txt)
        txt = re.sub(r"::: \{\.callout-tip[^\n]*\n## Descargar el libro.*?\n:::\n", "", txt, flags=re.S)
        txt = re.sub(r"## Tu progreso y uso sin conexión.*?(?=\n## )", "", txt, flags=re.S)
    txt = txt.replace("Answer all the questions and press **Show answers**. It does not count towards your grade.",
                      "Answer on paper and then check with the explanations in the box. In the web version these questions are marked automatically. They do not count towards your grade.")
    txt = txt.replace("Responde a todas las preguntas y pulsa **Mostrar respuestas**: verás en verde las acertadas, en rojo las falladas y tu recuento. Puedes corregir y volver a comprobar. No cuenta para la nota.",
                      "Responde en el papel y comprueba después con las explicaciones del recuadro. En la versión web estas preguntas se corrigen automáticamente. No cuentan para la nota.")
    # Quarto trata .solution como entorno de demostración: se renombra para el filtro libro-pdf
    txt = re.sub(r"\{\s*\.solution exercise=", "{.solucion-ejercicio exercise=", txt)
    # en Typst los títulos .unnumbered pierden su etiqueta: sin numeración no hace falta la clase
    txt = re.sub(r"\{(#[^ }]+) \.unnumbered\}", r"{\1}", txt)
    partes.append(txt)
doc = "\n\n{{< pagebreak >}}\n\n".join(partes)

autor = libro["author"][0]
cabecera = {
    "title": libro["title"],
    "subtitle": libro.get("subtitle", ""),
    "author": [{"name": autor["name"], "orcid": str(autor["orcid"]), "url": autor.get("url"),
                "affiliation": autor.get("affiliation")}],
    "date": "last-modified",
    "date-format": tr("D [de] MMMM [de] YYYY", "D MMMM YYYY"),
    "lang": tr("es", "en"),
    "engine": "markdown",
    "filters": ["webex", "interactivos", "libro-pdf"],
    "libro-pdf": {"web": WEB, "capitulos": {c: (cabecera_cap(c)[1] or "") for c in capitulos}},
    "format": {"typst": {
        "toc": True, "toc-depth": 1, "toc-title": tr("Índice", "Contents"),
        "papersize": "a4", "fontsize": "10.5pt",
        "margin": {"x": "2.3cm", "y": "2.5cm"},
        "fig-format": "svg", "code-overflow": "wrap",
        "output-file": f"{SLUG}.pdf",
    },
    "epub": {
        "toc": True, "toc-depth": 1, "toc-title": tr("Índice", "Contents"),
        "cover-image": "portada.png",
        "identifier": ("doi:" + str(libro["doi"])) if libro.get("doi") else CFG["web"],
        "publisher": "Pablo Sánchez-Núñez",
        "rights": "CC BY 4.0",
        "subject": CFG.get("materias", ""),
        "output-file": f"{SLUG}.epub",
    }},
}

if libro.get("doi"):
    cabecera["doi"] = libro["doi"]

if BUILD.exists():
    shutil.rmtree(BUILD)
(BUILD / "_extensions").mkdir(parents=True)
for ext in ("webex", "interactivos", "libro-pdf"):
    shutil.copytree(RAIZ / "_extensions" / ext, BUILD / "_extensions" / ext)
if (RAIZ / "figuras").exists():
    shutil.copytree(RAIZ / "figuras", BUILD / "figuras")
(BUILD / "_quarto.yml").write_text("project:\n  type: default\n")
(BUILD / "libro.qmd").write_text("---\n" + yaml.safe_dump(cabecera, allow_unicode=True, sort_keys=False) + "---\n\n" + doc)


def portada(destino):
    """Portada sencilla para el EPUB (1600 × 2400 px)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = ["Inter", "DejaVu Sans"]
    fig = plt.figure(figsize=(8, 12), dpi=200)
    fig.patch.set_facecolor("#000e78")
    fig.text(0.08, 0.80, CFG["titulo_portada"], color="white",
             fontsize=34, fontweight="bold", va="top", linespacing=1.15)
    fig.text(0.08, 0.60, CFG.get("subtitulo_portada", libro.get("subtitle", "")), color="#c9d2ff", fontsize=20, va="top", wrap=True)
    for i, c in enumerate(["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]):
        fig.patches.append(matplotlib.patches.Rectangle((0.08 + i * 0.09, 0.47), 0.07, 0.07,
                           transform=fig.transFigure, facecolor=c, edgecolor="none"))
    fig.text(0.08, 0.235, "Pablo Sánchez-Núñez", color="white", fontsize=22, fontweight="bold")
    fig.text(0.08, 0.11, "Universidad Carlos III de Madrid", color="#c9d2ff", fontsize=15)
    fig.text(0.08, 0.205, "ORCID 0000-0001-7845-9506", color="#c9d2ff", fontsize=13)
    fig.text(0.08, 0.175, "pablosancheznunez.com", color="#c9d2ff", fontsize=13)
    fig.text(0.08, 0.06, ("DOI " + str(libro["doi"]) + " · " if libro.get("doi") else "") + "CC BY 4.0", color="#c9d2ff", fontsize=12)
    fig.savefig(destino, facecolor=fig.get_facecolor())
    plt.close(fig)

portada(BUILD / "portada.png")
SALIDA.parent.mkdir(exist_ok=True)
for formato, extension in (("typst", "pdf"), ("epub", "epub")):
    r = subprocess.run(["quarto", "render", "libro.qmd", "--to", formato], cwd=BUILD, capture_output=True, text=True)
    print(r.stdout[-1500:], r.stderr[-3000:])
    if r.returncode != 0:
        sys.exit(r.returncode)
    destino = SALIDA.with_suffix("." + extension)
    shutil.copy(BUILD / (SLUG + "." + extension), destino)
    print(extension.upper() + ":", destino, destino.stat().st_size // 1024, "KB")
