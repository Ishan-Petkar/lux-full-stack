"""Reusable pieces: product tile (whole image is the link), responsive grid, empty state, thumbnails, section title."""
import streamlit as st

from . import icons
from .state import S, esc, flash, go, img_html, money, safe, ss, uid


def avail_html(stock: int) -> str:
    if stock <= 0:
        return '<span class="avail out">Sold out</span>'
    if stock <= 3:
        return f'<span class="avail low">Only {stock} left</span>'
    return '<span class="avail">In stock</span>'


def quick_add(pid: str) -> None:
    if not ss.user:
        flash("warning", "Sign in to add items to your bag.")
        go("Auth")
        return
    _, ok = safe(S.cart.add, uid(), pid, 1)
    if ok:
        flash("success", "Added to your bag.")


def tile(p: dict, prefix: str, sim: float | None = None, why: str = "", note: str = "", add: bool = True) -> None:
    """Borderless tile: tall image on warm grey, brand / name / price in small caps. An invisible button covers the image."""
    sold = p["stock"] <= 0
    line = ""
    if sim is not None:
        line = f'<div class="tsim">Similarity {sim:.2f}' + (f" · {esc(why)}" if why else "") + "</div>"
    elif note:
        line = f'<div class="tsim">{esc(note)}</div>'
    with st.container(key=f"tile-{prefix}-{p['_id']}"):
        st.markdown(
            f'<div class="timg{" tsold-img" if sold else ""}">{img_html(p, 640)}</div>' + ('<span class="tsold">Sold out</span>' if sold else "")
            + f'<div class="tmeta"><div><div class="tbrand">{esc(p["brand"])}</div><div>{esc(p["name"])}</div></div><span></span></div>'
            f'<div class="tprice">{money(p["price"])}</div>{line}', unsafe_allow_html=True)
        st.button("View", key=f"{prefix}-{p['_id']}", on_click=go, args=("Product", p["_id"]))
        if add and not sold:
            st.button("+", key=f"qa-{prefix}-{p['_id']}", on_click=quick_add, args=(p["_id"],), help="Add to bag")


def grid(items: list[dict], prefix: str, **kw) -> None:
    """One wrapping row of equal columns; the column count adapts to the viewport in CSS (5 / 4 / 3 / 2)."""
    if not items:
        return
    with st.container(key=f"grid-{prefix}"):
        cols = st.columns(len(items))
        for col, p in zip(cols, items):
            with col:
                tile(p, prefix, **kw)


def empty_state(title: str, text: str, button: str | None = None, target: str = "Catalog", icon_name: str = "box") -> None:
    st.markdown(f'<div class="empty">{icons.icon(icon_name, 36, 1.1)}<h3>{esc(title)}</h3><div class="muted">{esc(text)}</div></div>', unsafe_allow_html=True)
    if button:
        _, c, _ = st.columns([2, 1, 2])
        c.button(button, key=f"empty_{button}", on_click=go, args=(target,), use_container_width=True)


def thumb(p: dict, small: bool = False) -> str:
    return f'<div class="thumb{" sm" if small else ""}">{img_html(p, 160)}</div>'


def section_title(title: str, sub: str = "") -> None:
    st.markdown(f'<div class="sec-title">{esc(title)}' + (f"<small>{esc(sub)}</small>" if sub else "") + "</div>", unsafe_allow_html=True)
