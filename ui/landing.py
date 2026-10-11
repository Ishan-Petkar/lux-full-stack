"""Landing page: full-bleed campaign slides in the manner of a fashion house site.

A giant wordmark stays pinned and inverts over the imagery (mix-blend-mode), each campaign image unfolds from a framed crop as it
scrolls into view, a wall of product images sits edge to edge, and the page ends in quiet service notes. CSS only, no JavaScript.
"""
import base64
import io
from functools import lru_cache

import streamlit as st
from PIL import Image

from shop import config
from shop.seed_data import featured_ids
from .components import grid, section_title
from .state import S, esc, go, ss

HERO_DIR = config.ROOT / "assets" / "hero"


@lru_cache(maxsize=16)
def _bg(name: str, width: int) -> str:
    p = HERO_DIR / name
    if not p.is_file():
        return ""
    im = Image.open(p).convert("RGB")
    im.thumbnail((width, width))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=76, optimize=True, progressive=True)
    return "background-image:url(data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode() + ")"


def _go(cat: str, sub: str = "All") -> None:
    ss["cat"], ss["sub"], ss["q"], ss.shown = cat, sub, "", 16
    go("Catalog")


def slide(key: str, img: str, kicker: str, title: str, cta: str, cat: str, first: bool = False, half: bool = False, width: int = 2000) -> None:
    with st.container(key=f"zs-{key}"):
        st.markdown(f'<div class="zs{" first" if first else ""}{" half" if half else ""}"><div class="zi" style="{_bg(img, width)}"></div>'
                    f'<div class="zcap"><div class="k">{esc(kicker)}</div><div class="t">{esc(title)}</div></div></div>', unsafe_allow_html=True)
        st.button(cta, key=f"zb-{key}", on_click=_go, args=(cat,))


def page_home() -> None:
    st.markdown('<div class="zmark">curio</div>', unsafe_allow_html=True)
    ids = featured_ids()
    feats = [p for p in (S.repo.col.find_one({"_id": i}) for i in ids) if p]
    wall = [p for p in S.repo.col.find({"stock": {"$gt": 0}}).sort("_id", 1)]
    step = max(1, len(wall) // 12)
    mosaic = wall[::step][:12]

    slide("hero", "hero.jpg", "Autumn Winter", "The Collection", "Discover", "All", first=True)
    with st.container(key="grid-mosaic"):
        cols = st.columns(6)
        for col, p in zip(cols * 2, mosaic):
            with col:
                from .components import tile
                tile(p, "mo", add=False)
    slide("watch", "watch.jpg", "Haute horlogerie", "The Watch Edit", "Shop watches", "Watches")
    a, b = st.columns(2, gap="small")
    with a:
        slide("bags", "bags.jpg", "Maroquinerie", "Icons in leather", "Shop bags", "Bags", half=True, width=1300)
    with b:
        slide("jewel", "jewel.jpg", "Haute joaillerie", "Gold, worn daily", "Shop jewellery", "Jewellery", half=True, width=1300)
    slide("scent", "scent.jpg", "Parfumerie", "Signature scents", "Shop fragrance", "Fragrance")
    section_title("New arrivals", "Selected pieces")
    grid([p for p in feats if p["stock"] > 0][:4], "lp")
    slide("atelier", "atelier.jpg", "Tailoring & knitwear", "The Atelier", "Shop apparel", "Apparel")
    st.markdown('<div class="lp-svc"><div><b>Insured delivery</b><span>Complimentary above ₹10,000</span></div>'
                '<div><b>Verified payments</b><span>Signature-checked, nothing stored</span></div>'
                '<div><b>Cancel before dispatch</b><span>Full refund to the original method</span></div></div>', unsafe_allow_html=True)
