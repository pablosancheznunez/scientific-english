"""Genera las figuras del libro (SVG) en figuras/.

Uso, desde la raíz del libro:   python3 herramientas/figuras.py [--png]
Paleta categórica validada (orden fijo): azul, naranja, aguamarina, amarillo, magenta.
"""
import pathlib, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch

RAIZ = pathlib.Path(__file__).resolve().parent.parent
OUT = RAIZ / "figuras"; OUT.mkdir(exist_ok=True)

S = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
TINTA, TINTA2, GRIS, SUP = "#0b0b0b", "#52514e", "#d9d8d4", "#ffffff"
CAJA, CAJA2 = "#eef0f6", "#c9cfe0"

plt.rcParams.update({
    "font.family": ["Inter", "DejaVu Sans"], "font.size": 11,
    "svg.fonttype": "path", "figure.facecolor": SUP, "axes.facecolor": SUP,
})


def lienzo(w, h, xlim, ylim):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect("equal"); ax.axis("off")
    return fig, ax


def guardar(fig, nombre):
    fig.savefig(OUT / nombre, format="svg", bbox_inches="tight", pad_inches=0.15)
    if "--png" in sys.argv:
        pathlib.Path("/tmp/figpng").mkdir(exist_ok=True)
        fig.savefig(pathlib.Path("/tmp/figpng") / nombre.replace(".svg", ".png"), dpi=100, bbox_inches="tight")
    plt.close(fig); print("ok", nombre)


def caja(ax, x, y, w, h, texto, fc=CAJA, ec=CAJA2, tc=TINTA, fs=10, r=0.08, lw=1.2, peso="normal"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw))
    if texto:
        ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center", fontsize=fs, color=tc,
                linespacing=1.2, fontweight=peso)


def flecha(ax, a, b, color=TINTA2, rad=0.0):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=12, color=color, lw=1.3,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=2, shrinkB=2))


def pagina(ax, x, y, w, h, titulo):
    caja(ax, x, y, w, h, None, fc=SUP, ec=TINTA2, r=0.06)
    ax.add_patch(FancyBboxPatch((x, y + h - 0.35), w, 0.35, boxstyle="round,pad=0,rounding_size=0.06",
                                fc=CAJA, ec=TINTA2, lw=1.2))
    ax.text(x + 0.15, y + h - 0.175, titulo, ha="left", va="center", fontsize=9, color=TINTA2)
    for i in range(5):
        ax.plot([x + 0.2, x + w - 0.2 - (0.5 if i % 2 else 0)], [y + h - 0.7 - i * 0.32] * 2,
                color=GRIS, lw=3, solid_capstyle="round")





def e1_hourglass():
    from matplotlib.patches import Polygon
    fig, ax = lienzo(7.4, 5.2, (0, 12), (0, 9))
    ax.add_patch(Polygon([(1, 8.6), (11, 8.6), (7.2, 5.6), (4.8, 5.6)], closed=True, fc=S[0], alpha=0.2, ec="none"))
    ax.add_patch(Polygon([(4.8, 5.4), (7.2, 5.4), (7.2, 3.6), (4.8, 3.6)], closed=True, fc=S[2], alpha=0.25, ec="none"))
    ax.add_patch(Polygon([(4.8, 3.4), (7.2, 3.4), (11, 0.4), (1, 0.4)], closed=True, fc=S[3], alpha=0.22, ec="none"))
    for y, t, st in ((7.7, "Introduction", "field → gap → aim"), (4.5, "Methods\nand results", ""), (1.5, "Discussion", "findings → implications")):
        ax.text(6, y, t, ha="center", va="center", fontsize=12.5, fontweight="bold", color=TINTA, linespacing=1.1)
        if st: ax.text(6, y - 0.75, st, ha="center", fontsize=10, color=TINTA2)
    ax.text(0.6, 8.75, "General", fontsize=9.5, color=TINTA2); ax.text(0.6, 0.0, "General", fontsize=9.5, color=TINTA2); ax.text(7.5, 4.45, "Specific", fontsize=9.5, color=TINTA2)
    guardar(fig, "e1_hourglass.svg")


if __name__ == "__main__":
    e1_hourglass()
