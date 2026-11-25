"""Exporta las preguntas de autoevaluación del libro a Moodle XML.

Lee el bloque ::: {.webex-check} de cada capítulo y las explicaciones de
::: {.webex-solution}, y escribe en moodle/ un fichero por capítulo y uno
con todo el banco. Cada pregunta conserva su explicación como
retroalimentación general.

  {{< torf ... >}}     -> truefalse
  {{< mcq ... >}}      -> multichoice (respuesta única)
  {{< longmcq ... >}}  -> multichoice (respuesta única)
  {{< fitb ... >}}     -> shortanswer

Uso:  python3 herramientas/moodle.py
"""
import html, pathlib, re, shlex, sys
import xml.dom.minidom

sys.path.insert(0, pathlib.Path(__file__).resolve().parent.as_posix())
from comun import RAIZ, cabecera, capitulos, config
CFG = config()
OUT = RAIZ / "moodle"; OUT.mkdir(exist_ok=True)
CAPS = [(q, re.sub(r"\s*\{[^}]*\}", "", cabecera(q)[0])) for q in capitulos(incluir_apendices=False)]
SC = re.compile(r"\{\{<\s*(torf|mcq|longmcq|fitb)\s+(.*?)\s*>\}\}")

def md(t):
    """Markdown en línea mínimo -> HTML."""
    t = html.escape(t.strip(), quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    return t

def args(s):
    pos, kw = [], {}
    for tok in shlex.split(s):
        if "=" in tok and not tok.startswith("*"):
            k, v = tok.split("=", 1); kw[k] = v
        else:
            pos.append(tok)
    return pos, kw

def bloque(texto, clase):
    m = re.search(r"::: \{[^}]*\." + clase + r"[^}]*\}\n(.*?)\n:::", texto, re.S)
    return m.group(1) if m else ""

def preguntas(qmd):
    s = (RAIZ / qmd).read_text()
    caja = bloque(s, "webex-check")
    expl = [l[2:].strip() for l in bloque(s, "webex-solution").splitlines() if l.startswith("- ")]
    items = []
    for linea in caja.splitlines():
        if re.match(r"^\d+\.\s", linea):
            items.append(re.sub(r"^\d+\.\s", "", linea))
        elif linea.strip().startswith("{{< longmcq") and items:
            items[-1] += " " + linea.strip()
    return items, expl

def q_xml(nombre, texto, sc, a, kw, fb):
    enun = md(SC.sub("" if sc == "longmcq" else "____", texto).strip())
    general = f"<generalfeedback format=\"html\"><text><![CDATA[{md(fb)}]]></text></generalfeedback>" if fb else ""
    cab = f'<name><text>{html.escape(nombre)}</text></name><questiontext format="html"><text><![CDATA[<p>{enun}</p>]]></text></questiontext>{general}<defaultgrade>1</defaultgrade><penalty>0.3333333</penalty><hidden>0</hidden>'
    if sc == "torf":
        v = a[0].lower() in ("true", "verdadero", "v")
        return (f'<question type="truefalse">{cab}'
                f'<answer fraction="{100 if v else 0}" format="moodle_auto_format"><text>true</text><feedback><text></text></feedback></answer>'
                f'<answer fraction="{0 if v else 100}" format="moodle_auto_format"><text>false</text><feedback><text></text></feedback></answer></question>')
    if sc in ("mcq", "longmcq"):
        ops = "".join(
            f'<answer fraction="{100 if o.startswith("*") else 0}" format="html"><text><![CDATA[{md(o.lstrip("*"))}]]></text><feedback format="html"><text></text></feedback></answer>'
            for o in a)
        return (f'<question type="multichoice">{cab}<single>true</single><shuffleanswers>true</shuffleanswers>'
                f'<answernumbering>abc</answernumbering>{ops}</question>')
    if sc == "fitb":
        usecase = "0" if kw.get("ignorecase") == "true" else "1"
        ops = "".join(f'<answer fraction="100" format="moodle_auto_format"><text>{html.escape(x)}</text><feedback><text></text></feedback></answer>' for x in a)
        return f'<question type="shortanswer">{cab}<usecase>{usecase}</usecase>{ops}</question>'

todo, total = [], 0
for qmd, titulo in CAPS:
    items, expl = preguntas(qmd)
    if not items:
        continue
    qs = []
    for i, it in enumerate(items):
        m = SC.search(it)
        if not m:
            continue
        a, kw = args(m.group(2))
        fb = expl[i] if i < len(expl) else ""
        qs.append(q_xml(f"{titulo} · P{i + 1}", it, m.group(1), a, kw, fb))
    cat = f'<question type="category"><category><text>$course$/top/{CFG["moodle"]}/{html.escape(titulo)}</text></category></question>'
    doc = '<?xml version="1.0" encoding="UTF-8"?><quiz>' + cat + "".join(qs) + "</quiz>"
    bonito = xml.dom.minidom.parseString(doc.encode()).toprettyxml(indent="  ")
    nombre = re.sub(r"[^a-z0-9]+", "_", qmd.replace(".qmd", "").lower())
    (OUT / f"autoevaluacion_{nombre}.xml").write_text(bonito)
    todo.append(cat + "".join(qs)); total += len(qs)
    print(f"{titulo}: {len(qs)} preguntas")
doc = '<?xml version="1.0" encoding="UTF-8"?><quiz>' + "".join(todo) + "</quiz>"
(OUT / "autoevaluacion_todo.xml").write_text(xml.dom.minidom.parseString(doc.encode()).toprettyxml(indent="  "))
print("Total:", total, "preguntas ->", OUT)
