"""Tiny matplotlib drawing helpers (Graphviz is not required)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyBboxPatch, Polygon, Rectangle

C = {  # fill, edge
    "ui": ("#dbe7f5", "#2563a8"), "proc": ("#e6dff0", "#6b46a8"), "data": ("#d3eaea", "#1f8a8a"),
    "flow": ("#d9eadf", "#2f7d4f"), "dec": ("#f6e6d0", "#b06a14"), "term": ("#2f7d4f", "#1f5a38"),
    "neutral": ("#f1f5f9", "#475569"), "red": ("#fde2e2", "#b42318"), "title": ("#1e3a5f", "#1e3a5f"),
}
INK = "#1e293b"


def canvas(w, h, title=None, sub=None):
    fig = plt.figure(figsize=(w / 10, h / 10), dpi=170)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis("off")
    if title:
        ax.text(w / 2, h - 3.2, title, ha="center", va="center", fontsize=15, fontweight="bold", color=C["title"][0])
    if sub:
        ax.text(w / 2, h - 7.2, sub, ha="center", va="center", fontsize=9, color="#475569")
    return fig, ax


def save(fig, path):
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    print("saved", path)


def box(ax, x, y, w, h, text="", kind="neutral", fs=9, bold=False, r=1.2, ls="-", lw=1.2, color=INK, align="center", va="center", z=2):
    fc, ec = C[kind]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw, ls=ls, zorder=z))
    if text:
        tx = x + w / 2 if align == "center" else x + 1.5
        ax.text(tx, y + h / 2, text, ha=align, va=va, fontsize=fs, fontweight="bold" if bold else "normal",
                color=color if kind != "term" else "white", zorder=z + 1, linespacing=1.35)


def diamond(ax, cx, cy, w, h, text, fs=8.5):
    fc, ec = C["dec"]
    ax.add_patch(Polygon([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)], fc=fc, ec=ec, lw=1.2, zorder=2))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=INK, zorder=3, linespacing=1.3)


def ellipse(ax, cx, cy, w, h, text, kind="ui", fs=8.5):
    fc, ec = C[kind]
    ax.add_patch(Ellipse((cx, cy), w, h, fc=fc, ec=ec, lw=1.2, zorder=2))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=INK, zorder=3, linespacing=1.3)


def line(ax, pts, arrow=True, color="#334155", ls="-", lw=1.2, style="-|>", label=None, lpos=None, lfs=8, ldx=0, ldy=1.2, lcolor=None, ms=10, z=1, lha="center"):
    xs, ys = zip(*pts)
    last = len(pts) - 1
    ax.plot(xs[:-1] if arrow else xs, ys[:-1] if arrow else ys, color=color, ls=ls, lw=lw, zorder=z, solid_capstyle="butt")
    if arrow:
        ax.plot(xs[-2:-1] + xs[-1:], ys[-2:-1] + ys[-1:], color="none")
        ax.annotate("", xy=pts[-1], xytext=pts[-2], arrowprops=dict(arrowstyle=style, color=color, lw=lw, ls=ls, mutation_scale=ms, shrinkA=0, shrinkB=0), zorder=z)
    if label:
        if lpos is None:
            i = max(range(last), key=lambda k: abs(pts[k + 1][0] - pts[k][0]) + abs(pts[k + 1][1] - pts[k][1]))
            lx, ly = (pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2
        else:
            lx, ly = lpos
        ax.text(lx + ldx, ly + ldy, label, ha=lha, va="center", fontsize=lfs, color=lcolor or color, zorder=5,
                bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))


def table(ax, x, ytop, w, title, rows, kind="data", rh=2.7, fs=8):
    """ERD entity: header + rows [(name, type, key)] -> returns (x, ybottom, w, h)."""
    fc, ec = C[kind]
    hh = 3.6
    h = hh + rh * len(rows)
    ax.add_patch(Rectangle((x, ytop - h), w, h, fc="white", ec=ec, lw=1.4, zorder=2))
    ax.add_patch(Rectangle((x, ytop - hh), w, hh, fc=ec, ec=ec, zorder=3))
    ax.text(x + w / 2, ytop - hh / 2, title, ha="center", va="center", color="white", fontsize=9.5, fontweight="bold", zorder=4)
    for i, (n, t, k) in enumerate(rows):
        yc = ytop - hh - rh * (i + 0.5)
        if k:
            ax.add_patch(Rectangle((x, yc - rh / 2), w, rh, fc=fc, ec="none", zorder=2.5, alpha=0.55))
        ax.text(x + 1.2, yc, (f"{k}  " if k else "") + n, va="center", fontsize=fs, color=INK, zorder=4,
                fontweight="bold" if "PK" in (k or "") else "normal")
        ax.text(x + w - 1.2, yc, t, va="center", ha="right", fontsize=fs - 0.5, color="#64748b", zorder=4, family="monospace")
        ax.plot([x, x + w], [yc - rh / 2] * 2, color="#e2e8f0", lw=0.6, zorder=3)
    return x, ytop - h, w, h


def class_box(ax, x, ytop, w, name, attrs, methods, kind="proc", stereotype=None, fs=7.8, lh=2.25):
    fc, ec = C[kind]
    hh = 3.6 + (2.0 if stereotype else 0)
    ha, hm = max(1, len(attrs)) * lh + 1, max(1, len(methods)) * lh + 1
    h = hh + ha + hm
    y = ytop - h
    ax.add_patch(Rectangle((x, y), w, h, fc="white", ec=ec, lw=1.4, zorder=2))
    ax.add_patch(Rectangle((x, ytop - hh), w, hh, fc=fc, ec=ec, lw=1.4, zorder=3))
    if stereotype:
        ax.text(x + w / 2, ytop - 1.4, f"«{stereotype}»", ha="center", va="center", fontsize=7.2, style="italic", color=INK, zorder=4)
    ax.text(x + w / 2, ytop - hh + 1.9, name, ha="center", va="center", fontsize=9.2, fontweight="bold", color=INK, zorder=4)
    for i, a in enumerate(attrs):
        ax.text(x + 1, ytop - hh - lh * (i + 0.7), a, va="center", fontsize=fs, color=INK, zorder=4, family="monospace")
    ax.plot([x, x + w], [ytop - hh - ha] * 2, color=ec, lw=1.0, zorder=3)
    for i, m in enumerate(methods):
        ax.text(x + 1, ytop - hh - ha - lh * (i + 0.7), m, va="center", fontsize=fs, color=INK, zorder=4, family="monospace")
    return x, y, w, h


def actor(ax, x, y, name, s=1.0):
    ax.add_patch(plt.Circle((x, y + 9 * s), 1.7 * s, fc="white", ec=INK, lw=1.4, zorder=3))
    ax.plot([x, x], [y + 7.3 * s, y + 2.8 * s], color=INK, lw=1.4, zorder=3)
    ax.plot([x - 2.6 * s, x + 2.6 * s], [y + 5.8 * s] * 2, color=INK, lw=1.4, zorder=3)
    ax.plot([x, x - 2.4 * s], [y + 2.8 * s, y], color=INK, lw=1.4, zorder=3)
    ax.plot([x, x + 2.4 * s], [y + 2.8 * s, y], color=INK, lw=1.4, zorder=3)
    ax.text(x, y - 2.0, name, ha="center", va="center", fontsize=9, fontweight="bold", color=INK)


def legend(ax, x, y, items, fs=8):
    for i, (k, t) in enumerate(items):
        fc, ec = C[k]
        ax.add_patch(Rectangle((x + i * 34, y), 2.4, 2.4, fc=fc, ec=ec, lw=1))
        ax.text(x + i * 34 + 3.6, y + 1.2, t, va="center", fontsize=fs, color="#475569")
