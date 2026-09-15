"""Shared chart chrome for the run's figures (light mode, static PNG, deck-ready).

Palette follows the dataviz method's reference instance: categorical slots in fixed order (blue, orange, aqua —
all-pairs-safe cap of three for scatter forms), a sequential blue ramp and ink/grid tokens. Text wears ink tokens,
never series colours. Every figure gets a short bold headline, an optional subtitle and a one-line source footer;
all three are wrapped to the canvas width and kept inside it, so the exported PNG is the size the figure was
designed at (roughly 16:9, 200 dpi) instead of being stretched by a long caption."""

import os
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASE = "#c3c2b7"
ABSENT = "#f0efec"

BLUE = "#2a78d6"  # categorical slot 1
ORANGE = "#eb6834"  # slot 2
AQUA = "#1baf7a"  # slot 3
BLUE_DARK = "#1c5cab"  # sequential 550
BLUE_LIGHT = "#86b6ef"  # sequential 250
DEEMPH = "#c3c2b7"  # de-emphasis gray for context marks

DPI = 200
DECK = os.environ.get("FIG_DECK") == "1"  # deck variant: the slide carries the title, so the figure omits it
TITLE_PT, SUB_PT, FOOT_PT = 15.5, 11.0, 8.5
FONT = ["Helvetica Neue", "Arial", "DejaVu Sans"]
plt.rcParams.update(
    {
        "font.family": FONT,
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.dpi": DPI,
        "savefig.dpi": DPI,
    }
)


def new_fig(w=11.0, h=6.2):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    style_ax(ax)
    return fig, ax


def style_ax(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(BASE)
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=MUTED, labelsize=10, length=3)
    ax.grid(True, color=GRID, linewidth=0.6, alpha=0.9)
    ax.set_axisbelow(True)


def wrap(text, fig_w, pt):
    """Wrap `text` to the canvas width for a font of `pt` points (about 125/pt characters per inch, half-inch margins)."""
    n = max(30, int((fig_w - 0.5) * 125 / pt))
    return "\n".join(textwrap.fill(p, n) if p else "" for p in str(text).split("\n"))


def _lines_in(pt, text):
    return (text.count("\n") + 1) * pt * 1.32 / 72  # inches of vertical space, 1.32 line spacing


def headline(fig, title, subtitle=None, footer=None):
    """Bold left-aligned title, optional subtitle (ink-2) and source footer (muted), all inside the canvas.
    Returns the rect to pass to tight_layout so the axes leave room for them."""
    w, h = fig.get_size_inches()
    t = wrap(title, w, TITLE_PT)
    s = wrap(subtitle, w, SUB_PT) if subtitle else None
    f = wrap(footer, w, FOOT_PT) if footer else None
    y = h - 0.12
    if not DECK:
        fig.text(0.012, y / h, t, fontsize=TITLE_PT, color=INK, ha="left", va="top", weight="bold", linespacing=1.32)
        y -= _lines_in(TITLE_PT, t) + 0.06
    if s:
        fig.text(0.012, y / h, s, fontsize=SUB_PT, color=INK2, ha="left", va="top", linespacing=1.32)
        y -= _lines_in(SUB_PT, s) + 0.04
    top = (y - 0.10) / h
    bottom = 0.04 / h
    if f:
        fig.text(0.012, 0.07 / h, f, fontsize=FOOT_PT, color=MUTED, ha="left", va="bottom", linespacing=1.32)
        bottom = (0.07 + _lines_in(FOOT_PT, f) + 0.10) / h
    return (0.0, bottom, 1.0, top)


def finish(fig, path, title, subtitle=None, footer=None):
    fig.tight_layout(rect=headline(fig, title, subtitle, footer))
    save(fig, path)


def title_caption(fig, ax, title, caption):  # kept for older callers: headline + footer, no subtitle
    fig.tight_layout(rect=headline(fig, title, None, caption))


def save(fig, path):
    fig.savefig(path, facecolor=SURFACE, dpi=DPI, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    print(f"figure → {path}")
