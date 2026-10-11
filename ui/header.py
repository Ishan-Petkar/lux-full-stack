"""Fixed header (menu, wordmark, search, bag, account) and the footer."""
import streamlit as st

from shop import config
from .state import S, esc, go, is_admin, safe, ss, uid


def _open_cat(cat: str) -> None:
    ss["cat"], ss["sub"], ss["q"], ss.shown = cat, "All", "", 16
    go("Catalog")


def _on_search() -> None:
    """A search from the header always looks across the whole catalogue."""
    ss.view, ss.shown = "Catalog", 16
    ss["cat"], ss["sub"] = "All", "All"


def header() -> None:
    bag = 0
    if ss.user:
        v, _ = safe(S.cart.view, uid())
        bag = v["count"] if v else 0
    with st.container(key="hdr"):
        c1, c2, c3, c4, c5 = st.columns([0.7, 2.6, 2.0, 0.9, 1.3], vertical_alignment="center")
        with c1.popover("", icon=":material/drag_handle:"):
            st.markdown("<div class='up small muted' style='margin-bottom:.6rem'>Menu</div>", unsafe_allow_html=True)
            st.button("[01]  All", key="nav_Shop", on_click=_open_cat, args=("All",), type="tertiary")
            for i, cat in enumerate(S.repo.categories(), 2):
                st.button(f"[{i:02d}]  {cat}", key=f"menu_{i}", on_click=_open_cat, args=(cat,), type="tertiary")
            st.markdown("<hr class='rule'>", unsafe_allow_html=True)
            st.button("Home", key="nav_Home", on_click=go, args=("Home",), type="tertiary")
            st.button("Wishlist", key="nav_Wish", on_click=go, args=("Account",), kwargs={"account_tab": "Wishlist"}, type="tertiary")
            st.button("Orders", key="nav_Orders", on_click=go, args=("Account",), kwargs={"account_tab": "Orders"}, type="tertiary")
            if is_admin():
                st.button("Admin console", key="nav_Admin", on_click=go, args=("Admin",), type="tertiary")
            st.button("Help", key="nav_Help", on_click=go, args=("Help",), type="tertiary")
        c2.button("curio", key="brand", on_click=go, args=("Home",), type="tertiary")
        c3.text_input("Search", key="q", placeholder="Search", label_visibility="collapsed", max_chars=config.MAX_QUERY_LEN + 20, on_change=_on_search)
        c4.button(f"Bag ({bag})", key="bag", on_click=go, args=("Cart",), type="tertiary")
        label = ss.user["name"].split()[0] if ss.user else "Log in"
        c5.button(label, key="acct_btn", on_click=go, args=("Account" if ss.user else "Auth",), kwargs={"account_tab": "Orders"}, type="tertiary")


def footer() -> None:
    cats = "".join(f"<span>{esc(c)}</span>" for c in S.repo.categories()[:5])
    st.markdown(
        f'<div class="foot"><div class="foot-grid">'
        f'<div><b>Collections</b>{cats}</div>'
        f'<div><b>Help</b><span>Delivery &amp; returns</span><span>Payments (demo)</span><span>Test credentials</span></div>'
        f'<div><b>Maison curio</b><span>Insured delivery</span><span>Verified payments</span><span>Cancel before dispatch</span></div>'
        f'<div><b>About</b><span>MCA academic project</span><span>Python · Streamlit · MongoDB</span><span>Database: {esc(S.backend)}</span></div></div>'
        f'<div class="foot-small">Academic prototype: no real sales, payments or deliveries. Brand names, descriptions and photographs are used for illustration only; '
        f'curio is not affiliated with any maison shown. Prices are indicative. Sources and licences: assets/CREDITS.md.</div></div>', unsafe_allow_html=True)
