"""Category page (numbered index + tile grid) and product page (large image, pinned details, bought together, similar, reviews)."""
from datetime import date, timedelta

import streamlit as st

from shop import config, pricing
from shop.brands import facts
from shop.catalog import SORTS
from shop.errors import ShopError
from shop.validators import clean_pincode
from . import icons
from .components import avail_html, empty_state, grid, section_title, tile
from .state import PAGE_SIZE, S, esc, flash, go, img_html, money, safe, show_flash, ss, uid


# --------------------------------------------------------------------- category page
def _pick(cat: str, sub: str = "All") -> None:
    ss["cat"], ss["sub"], ss.shown, ss["q"] = cat, sub, PAGE_SIZE, ""


def page_catalog() -> None:
    cats = S.repo.categories()
    cat = ss.get("cat", "All")
    sub = ss.get("sub", "All")
    query = ss.get("q", "")
    lo, hi = S.repo.price_bounds()
    title = f"“{query.strip()}”" if query.strip() else (sub if sub != "All" else (cat if cat != "All" else "All"))

    st.markdown(f'<div class="title-d">{esc(title)}</div>', unsafe_allow_html=True)
    left, right = st.columns([1.15, 6], gap="medium")
    with left:
        with st.container(key="index"):
            st.button("[01]  View all", key="idx_all", on_click=_pick, args=("All",), type="primary" if cat == "All" else "tertiary")
            for i, c in enumerate(cats, 2):
                active = cat == c
                st.button(f"[{i:02d}]  {c}", key=f"idx_{i}", on_click=_pick, args=(c,), type="primary" if active else "tertiary")
                if active:
                    for s_ in S.repo.subcategories(c):
                        st.button(f"— {s_}", key=f"sub_{s_}", on_click=_pick, args=(c, s_), type="primary" if sub == s_ else "tertiary")
    with right:
        with st.container(key="tools"):
            t1, t2, t3, t4 = st.columns([3, 1.6, 1.1, 1])
            sort = t2.selectbox("Sort by", list(SORTS), label_visibility="collapsed")
            in_stock = t3.toggle("In stock")
            with t4.popover("Filters", icon=":material/tune:"):
                brands = st.multiselect("Maison", S.repo.brands(cat), key="f_brands")
                price = st.slider("Price", lo, hi, (lo, hi), step=5000, key="f_price")
        sig = (query, cat, sub, sort, in_stock, tuple(brands), price)
        if sig != ss.filter_sig:
            ss.filter_sig, ss.shown = sig, PAGE_SIZE
        items, ok = safe(S.repo.search, query, cat, in_stock, sort, brands or None, price if price != (lo, hi) else None,
                         S.bundles.popularity() if sort == "Best sellers" else None, sub)
        show_flash()
        if not ok:
            return
        t1.markdown(f"<span class='muted up small'>{len(items)} piece(s)</span>", unsafe_allow_html=True)
        if not items:
            empty_state("No pieces found", "Try different words or clear the filters.", "View all", "Catalog", "gem")
            return
        grid(items[:ss.shown], "cat")
        if len(items) > ss.shown:
            _, c, _ = st.columns([2, 1, 2])
            c.button(f"View more ({len(items) - ss.shown})", key="more", use_container_width=True,
                     on_click=lambda: ss.__setitem__("shown", ss.shown + PAGE_SIZE))


# --------------------------------------------------------------------- product page
def _add(pid: str, qty) -> None:
    if not ss.user:
        flash("warning", "Sign in to add items to your bag. A demo account is one click away.")
        go("Auth")
        return
    _, ok = safe(S.cart.add, uid(), pid, qty)
    if ok:
        flash("success", "Added to your bag.")


def _add_set(pids: list[str]) -> None:
    if not ss.user:
        flash("warning", "Sign in to add items to your bag.")
        go("Auth")
        return
    n = sum(1 for pid in pids if safe(S.cart.add, uid(), pid, 1)[1])
    if n:
        flash("success", f"Added {n} piece(s) to your bag.")


def _wish(pid: str) -> None:
    if not ss.user:
        flash("warning", "Sign in to save pieces to your wishlist.")
        go("Auth")
        return
    saved, ok = safe(S.wishlist.toggle, uid(), pid)
    if ok:
        flash("success", "Saved to your wishlist." if saved else "Removed from your wishlist.")


def _bought_together(p: dict) -> None:
    rows = [r for r in S.bundles.together(p["_id"], k=6) if S.repo.col.find_one({"_id": r["product_id"], "stock": {"$gt": 0}})][:3]
    if not rows or p["stock"] <= 0:
        return
    parts = [p] + [S.repo.get(r["product_id"]) for r in rows]
    section_title("Frequently bought together", "Most people who buy this piece also buy these")
    with st.container(key="grid-bt"):
        cols = st.columns(len(parts))
        for i, (col, x) in enumerate(zip(cols, parts)):
            with col:
                tile(x, "bt", note="This piece" if i == 0 else f"In {rows[i - 1]['confidence'] * 100:.0f}% of orders with this piece", add=False)
    total = sum(x["price"] for x in parts)
    _, c, _ = st.columns([1.5, 1.4, 1.5])
    c.markdown(f"<div class='ra' style='text-align:center;margin:.8rem 0 .4rem'>Set of {len(parts)} · {money(total)}</div>", unsafe_allow_html=True)
    c.button("Add all to bag", key="fbt_add", on_click=_add_set, args=([x["_id"] for x in parts],), use_container_width=True, type="primary")
    st.markdown("<div class='sub-c' style='margin-top:.8rem;text-transform:none'>Market-basket analysis of past orders (confidence and lift). The starting history is synthetic; real orders placed here are added to it.</div>",
                unsafe_allow_html=True)


def _reviews(p: dict) -> None:
    section_title("Reviews")
    summ = S.reviews.summary(p["_id"])
    a, b = st.columns([1, 2.4], gap="large")
    with a:
        if summ["count"]:
            bars = "".join(f'<div class="bar"><span>{i}</span><div><i style="width:{summ["hist"][i] / summ["count"] * 100:.0f}%"></i></div>'
                           f'<span class="muted">{summ["hist"][i]}</span></div>' for i in range(5, 0, -1))
            st.markdown(f'<div style="font-family:var(--didone);font-size:2.4rem;line-height:1">{summ["avg"]:.1f}</div>{icons.stars(summ["avg"], None, 14)}'
                        f'<div class="muted small">{summ["count"]} review(s)</div><div style="margin-top:.8rem">{bars}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="muted">No reviews yet.</div>', unsafe_allow_html=True)
        if ss.user:
            with st.popover("Write a review", use_container_width=True):
                with st.form(f"rev-{p['_id']}", border=False):
                    stars = st.feedback("stars", key=f"stars-{p['_id']}")
                    title = st.text_input("Title", max_chars=80)
                    body = st.text_area("Your review", max_chars=1500)
                    if st.form_submit_button("Submit review", type="primary"):
                        _, ok = safe(S.reviews.add, ss.user, p["_id"], (stars + 1) if stars is not None else 0, title, body)
                        if ok:
                            flash("success", "Thank you for your review.")
                            st.rerun()
                        show_flash()
        else:
            st.caption("Log in to write a review.")
    with b:
        for r in S.reviews.for_product(p["_id"], 8):
            st.markdown(f'<div class="rev"><div class="rev-head">{icons.stars(r["rating"], None, 12)}<b class="up">{esc(r["title"])}</b>'
                        + ('<span class="verified">Verified purchase</span>' if r.get("verified") else "")
                        + f'</div><div class="rev-body">{esc(r["body"])}</div><div class="muted small">{esc(r["user_name"])} · {r["created_at"]:%d %b %Y}</div></div>',
                        unsafe_allow_html=True)


def page_product() -> None:
    pid = ss.selected
    p, ok = safe(S.repo.get, pid) if pid else (None, False)
    if not ok:
        show_flash()
        empty_state("Piece not found", "It may have been removed.", "Back to the collection")
        return
    show_flash()
    left, right = st.columns([1.25, 1], gap="large")
    with left:
        st.markdown(f'<div class="pimgbig">{img_html(p, 1100)}</div>', unsafe_allow_html=True)
    with right:
        with st.container(key="pinfo"):
            summ = S.reviews.summary(pid)
            rating = icons.stars(summ["avg"], summ["count"], 13) if summ["count"] else ""
            st.markdown(f'<div class="pbrand-lg">{esc(p["brand"])}</div><h1 class="pname-lg" style="margin:.1rem 0 0 !important">{esc(p["name"])}</h1>'
                        f'<div class="pprice-lg">{money(p["price"])}</div><div class="ptax">MRP incl. of all taxes · indicative price</div>'
                        f'<div style="margin:.5rem 0">{rating} &nbsp; {avail_html(p["stock"])}</div><hr class="rule">', unsafe_allow_html=True)
            if p["stock"] > 0:
                q1, q2, q3 = st.columns([1, 3, 0.8], vertical_alignment="bottom")
                qty = q1.number_input("Qty", 1, min(p["stock"], config.MAX_LINE_QTY), 1, key=f"qty-{pid}")
                q2.button("Add", key=f"add-{pid}", on_click=_add, args=(pid, qty), use_container_width=True)
                saved = bool(ss.user) and pid in S.wishlist.ids(uid())
                q3.button("", key=f"wish-{pid}", icon=":material/bookmark:" if saved else ":material/bookmark_border:", on_click=_wish, args=(pid,),
                          type="tertiary", help="Wishlist")
            else:
                st.markdown('<div class="avail out">Currently sold out</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="pdesc">{esc(p["description"])}</div>'
                        f'<dl class="facts"><dt>Maison</dt><dd>{esc(facts(p["brand"]) or p["brand"])}</dd><dt>Collection</dt><dd>{esc(p["category"])} · {esc(p.get("subcategory") or "")}</dd>'
                        f'<dt>Reference</dt><dd>{esc(pid)}</dd></dl>', unsafe_allow_html=True)
            with st.expander("Delivery to your PIN code"):
                pin = st.text_input("PIN code", placeholder="411045", max_chars=6, key=f"pin-{pid}", label_visibility="collapsed")
                if pin:
                    try:
                        code = clean_pincode(pin)
                        f = lambda n: (date.today() + timedelta(days=n)).strftime("%a %d %b")
                        lo, hi = pricing.eta_days(code, "standard")
                        elo, ehi = pricing.eta_days(code, "express")
                        st.markdown(f"Insured standard: {f(lo)} – {f(hi)}  \nPriority courier: {f(elo)} – {f(ehi)}")
                    except ShopError as exc:
                        st.markdown(f"<span class='avail low'>{esc(str(exc))}</span>", unsafe_allow_html=True)
            with st.expander("Shipping, exchanges and returns"):
                st.markdown(f"Insured delivery is complimentary above {config.CURRENCY}{config.FREE_SHIPPING_MIN:,}. Orders can be cancelled until dispatch with a full refund. "
                            "Delivery and refunds are simulated in this academic demo.")
            if p.get("source"):
                st.markdown(f"<div class='muted small' style='margin-top:.8rem'>Description: {esc(p['source'])}</div>", unsafe_allow_html=True)

    _bought_together(p)

    n = ss.get("top_n") or config.TOP_N
    res, ok2 = safe(S.reco.recommend, pid, n)
    section_title("You may also like", "Similar pieces by description · TF-IDF cosine similarity")
    _, c, _ = st.columns([3, 1.6, 3])
    c.segmented_control("Show", [4, 8], default=config.TOP_N, key="top_n", label_visibility="collapsed")
    if ok2 and res.items:
        if res.method != "content-based" and res.message:
            st.info(res.message)
        for start in range(0, len(res.items), 4):
            chunk = res.items[start:start + 4]
            with st.container(key=f"grid-rec{start}"):
                cols = st.columns(len(chunk))
                for col, rec in zip(cols, chunk):
                    with col:
                        tile(rec.product, "rec", sim=rec.score, why="; ".join(rec.reasons[:2]), add=False)
    _reviews(p)
