"""House style for 'The Two Ledgers' figures.

Palette and metrics read out of Muressons_Chapter04_Complete.docx, so figures
sit inside the text block rather than on top of it.

Accessibility rule (Outline v2, line 105): every figure must carry its
information in shape, label or position as well as colour. Nothing here may
rely on colour discrimination alone — hence HATCH, DASH and MARK, and direct
labelling in preference to legends.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import matplotlib.patheffects as pe
import os

# ── palette (hex values taken from the chapter template) ──────────────────
NAVY   = "#1F3A5F"   # headings, table header fill
SLATE  = "#2C3B49"   # body text
TEAL   = "#0E7C7B"   # section accent
RUST   = "#8A3B12"   # emphasis
ORANGE = "#B4531A"
GREY   = "#5A6B7B"
LGREY  = "#6B7A88"
PALE   = "#EDF2F5"   # box / table fill
WHITE  = "#FFFFFF"
INK    = SLATE

# Ordered series colours. Never the only difference between two series.
SERIES = [NAVY, TEAL, RUST, GREY, ORANGE, "#4A6FA5", "#7A5C3E"]
DASH   = ["-", "--", "-.", ":", (0, (5, 1, 1, 1)), (0, (3, 1, 3, 1, 1, 1)), (0, (1, 1))]
MARK   = ["o", "s", "^", "D", "v", "P", "X"]
HATCH  = ["", "///", "...", "xxx", "\\\\\\", "ooo", "++"]

TEXT_WIDTH_IN = 6.5          # the chapter text block
DPI = 300

FIGDIR = os.path.expanduser("~/mnt/muressons-sim/docs/figures")

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Carlito", "DejaVu Sans"],
    "font.size": 8.5,
    "axes.titlesize": 9.5,
    "axes.titleweight": "bold",
    "axes.labelsize": 8.5,
    "axes.edgecolor": GREY,
    "axes.labelcolor": INK,
    "axes.linewidth": 0.8,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": "#D6DEE4",
    "grid.linewidth": 0.6,
    "xtick.color": INK, "ytick.color": INK,
    "xtick.labelsize": 8, "ytick.labelsize": 8,
    "text.color": INK,
    "legend.frameon": False,
    "legend.fontsize": 8,
    "figure.dpi": DPI,
    "savefig.dpi": DPI,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.04,
})


def newfig(w=TEXT_WIDTH_IN, h=3.2, nrows=1, ncols=1, **kw):
    fig, ax = plt.subplots(nrows, ncols, figsize=(w, h), **kw)
    return fig, ax


def despine(ax, keep=("left", "bottom")):
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(s in keep)


def nogrid(ax):
    ax.grid(False)
    ax.set_xticks([]); ax.set_yticks([])
    despine(ax, keep=())


def label_line(ax, x, y, text, color, ha="left", va="center", dx=0.12, dy=0.0, size=8):
    """Direct label on a series — preferred over a legend."""
    t = ax.text(x + dx, y + dy, text, color=color, ha=ha, va=va,
                fontsize=size, fontweight="bold")
    t.set_path_effects([pe.withStroke(linewidth=2.2, foreground="white")])
    return t


def box(ax, x, y, w, h, text, fc=PALE, ec=NAVY, tc=INK, size=8, weight="normal",
        radius=0.02, lw=1.0, ls="-"):
    """A rounded node for schematic diagrams (axis coordinates)."""
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0,rounding_size={radius}",
                       linewidth=lw, edgecolor=ec, facecolor=fc, linestyle=ls,
                       mutation_aspect=1)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=size, color=tc, fontweight=weight, wrap=True, linespacing=1.25)
    return p


def arrow(ax, xy_from, xy_to, color=NAVY, lw=1.1, style="-|>", rad=0.0, ls="-"):
    a = FancyArrowPatch(xy_from, xy_to, arrowstyle=style, mutation_scale=9,
                        linewidth=lw, color=color, linestyle=ls,
                        connectionstyle=f"arc3,rad={rad}",
                        shrinkA=1.5, shrinkB=1.5)
    ax.add_patch(a)
    return a


def esc(s):
    """Literal dollar signs — two on one line would otherwise open mathtext."""
    return s.replace("$", r"\$")


def source(fig, text):
    """The provenance line. Every figure carries one."""
    fig.text(0.0, -0.015, esc(text), fontsize=7, color=GREY, ha="left", va="top",
             style="italic", wrap=True)


def venn_label_points(centres, r, lo=-2.2, hi=2.2, n=700):
    """Deepest interior point of every non-empty region of a 3-circle Venn.

    A region boundary is made only of circle arcs, so the distance from a point
    to its own region's edge is min_i | ||p - c_i|| - r |. Maximising that over
    the region puts each label where it cannot collide with an arc.
    Returns {membership_tuple: (x, y)}.
    """
    import numpy as _np
    g = _np.linspace(lo, hi, n)
    X, Y = _np.meshgrid(g, g)
    D = [_np.hypot(X - cx, Y - cy) for cx, cy in centres]
    inside = [d <= r for d in D]
    depth = _np.minimum.reduce([_np.abs(d - r) for d in D])
    out = {}
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                m = _np.ones_like(X, dtype=bool)
                for want, ins in zip((a, b, c), inside):
                    m &= ins if want else ~ins
                if not m.any():
                    continue
                dd = _np.where(m, depth, -1.0)
                i = _np.unravel_index(_np.argmax(dd), dd.shape)
                out[(bool(a), bool(b), bool(c))] = (float(X[i]), float(Y[i]))
    return out


def save(fig, name):
    """Write the PNG flattened to RGB.

    matplotlib writes RGBA even with an opaque facecolor, and LibreOffice
    renders an RGBA PNG in a Word file as a blank strip — which makes the
    proof-render useless. Flattening onto white costs nothing and the file
    then renders identically everywhere.
    """
    os.makedirs(FIGDIR, exist_ok=True)
    path = os.path.join(FIGDIR, name + ".png")
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    try:
        from PIL import Image
        im = Image.open(path)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            flat = Image.new("RGB", im.size, (255, 255, 255))
            flat.paste(im, mask=im.split()[-1])
            flat.save(path, dpi=(DPI, DPI))
    except Exception as exc:
        print("  ! flatten failed:", exc)
    print("  fig:", name)
    return path
