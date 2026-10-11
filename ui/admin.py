"""Admin console: dashboard, orders, products and coupons. Everything is gated on the admin role."""
import pandas as pd
import streamlit as st

from shop import media
from shop.errors import AuthError
from shop.orders import STATUS_FLOW, require_admin
from shop.stats import dashboard
from .components import empty_state
from .state import S, esc, flash, go, is_admin, money, safe, show_flash, ss


INK, GOLD, GREY = "#000000", "#b8892b", "#d9d9d9"
PALETTE = [INK, GOLD, "#707070", "#a9a9a9", "#cdb68a", "#3a3a3a", "#8b6a1f", "#c9c9c9"]


def _kpi(label: str, value: str, delta: float | None = None, sub: str = "") -> str:
    d = ""
    if delta is not None:
        d = f"<span class='kpi-d {'up' if delta >= 0 else 'down'}'>{'+' if delta >= 0 else ''}{delta:.1f}%</span>"
    return f"<div class='kpi'><div class='kpi-l'>{esc(label)}</div><div class='kpi-v'>{esc(value)}</div><div class='kpi-s'>{d} {esc(sub)}</div></div>"


def _style(chart, height: int = 280):
    return (chart.properties(height=height).configure_view(strokeWidth=0).configure_axis(labelFont="Inter", titleFont="Inter", labelFontSize=10,
            titleFontSize=10, gridColor="#eeeeee", domainColor="#bbbbbb", tickColor="#bbbbbb", labelColor="#555", titleColor="#555")
            .configure_legend(labelFont="Inter", titleFont="Inter", labelFontSize=10, orient="bottom", title=None))


def _inr(v: float) -> str:
    return f"₹{v / 10_000_000:.2f} Cr" if v >= 10_000_000 else (f"₹{v / 100_000:.1f} L" if v >= 100_000 else f"₹{v:,.0f}")


def _card(title: str, sub: str = "") -> None:
    st.markdown(f"<div class='ch-t'>{esc(title)}</div>" + (f"<div class='ch-s'>{esc(sub)}</div>" if sub else ""), unsafe_allow_html=True)


def _dashboard_tab() -> None:
    import altair as alt
    c1, c2, c3 = st.columns([2.5, 1.5, 1.4], vertical_alignment="center")
    c1.markdown("<span class='muted up small'>Figures are computed live from MongoDB</span>", unsafe_allow_html=True)
    days = c2.segmented_control("Period", [30, 90, 180], default=90, format_func=lambda d: f"{d} days", label_visibility="collapsed") or 90
    incl = c3.toggle("Include seeded history", value=True, help="About 850 synthetic past orders that bootstrap 'frequently bought together'. Switch off to see only orders placed in this app.")
    d = dashboard(S.db, incl, days)
    if not d["paid_orders"]:
        st.info("No paid orders yet. Switch on seeded history, or place an order as a customer.")
        return

    st.markdown("<div class='kpis'>"
                + _kpi("Revenue", _inr(d["revenue"]), d["delta_revenue"], f"vs previous {days} days")
                + _kpi("Orders", f"{d['paid_orders']:,}", d["delta_orders"], f"{d['orders'] - d['paid_orders']} not completed")
                + _kpi("Average order", _inr(d["aov"]), d["delta_aov"])
                + _kpi("Pieces sold", f"{d['units']:,}")
                + _kpi("Active buyers", f"{d['active_buyers']:,}", None, f"repeat rate {d['repeat_rate']}%" if d["repeat_rate"] is not None else f"in {days} days")
                + _kpi("Inventory value", _inr(d["inventory_value"]), None, f"{len(d['low_stock'])} low on stock") + "</div>", unsafe_allow_html=True)

    a, b = st.columns([2, 1], gap="large")
    with a:
        _card("Revenue by week", f"Last {days} days")
        wk = pd.DataFrame({"Week": list(d["weekly"]), "Revenue": list(d["weekly"].values())})
        wk["Week"] = pd.to_datetime(wk["Week"])
        base = alt.Chart(wk).encode(x=alt.X("Week:T", title=None, axis=alt.Axis(format="%d %b")), y=alt.Y("Revenue:Q", title=None, axis=alt.Axis(format="~s")),
                                    tooltip=[alt.Tooltip("Week:T", format="%d %b %Y"), alt.Tooltip("Revenue:Q", format=",.0f")])
        grad = alt.Gradient(gradient="linear", stops=[alt.GradientStop(color="#00000033", offset=0), alt.GradientStop(color="#00000000", offset=1)], x1=1, x2=1, y1=1, y2=0)
        area = base.mark_area(color=grad, line={"color": INK, "strokeWidth": 1.6}, interpolate="monotone")
        dots = base.mark_point(color=GOLD, filled=True, size=40)
        st.altair_chart(_style(area + dots, 300), use_container_width=True)
    with b:
        _card("Order status")
        sd = pd.DataFrame({"Status": list(d["by_status"]), "Orders": list(d["by_status"].values())})
        st.altair_chart(_style(alt.Chart(sd).mark_arc(innerRadius=62, outerRadius=105, stroke="#fff", strokeWidth=2).encode(
            theta="Orders:Q", color=alt.Color("Status:N", scale=alt.Scale(range=PALETTE)), tooltip=["Status", "Orders"]), 300), use_container_width=True)

    a, b = st.columns(2, gap="large")
    with a:
        _card("Revenue by collection")
        cd = pd.DataFrame({"Collection": list(d["category_revenue"]), "Revenue": list(d["category_revenue"].values())})
        bars = alt.Chart(cd).mark_bar(color=INK, cornerRadius=0, size=18).encode(
            y=alt.Y("Collection:N", sort="-x", title=None), x=alt.X("Revenue:Q", title=None, axis=alt.Axis(format="~s")), tooltip=["Collection", alt.Tooltip("Revenue:Q", format=",.0f")])
        st.altair_chart(_style(bars, 300), use_container_width=True)
    with b:
        _card("Top maisons by revenue")
        bd = pd.DataFrame({"Maison": list(d["brand_revenue"]), "Revenue": list(d["brand_revenue"].values())})
        bars = alt.Chart(bd).mark_bar(color=GOLD, size=18).encode(
            y=alt.Y("Maison:N", sort="-x", title=None), x=alt.X("Revenue:Q", title=None, axis=alt.Axis(format="~s")), tooltip=["Maison", alt.Tooltip("Revenue:Q", format=",.0f")])
        st.altair_chart(_style(bars, 300), use_container_width=True)

    a, b, c = st.columns([1.3, 1.3, 1], gap="large")
    with a:
        _card("Order value distribution", "Number of orders per value band")
        ov = pd.DataFrame({"Value": d["order_values"]})
        st.altair_chart(_style(alt.Chart(ov).mark_bar(color=INK).encode(x=alt.X("Value:Q", bin=alt.Bin(maxbins=24), title=None, axis=alt.Axis(format="~s")),
                                                                    y=alt.Y("count()", title=None)), 260), use_container_width=True)
    with b:
        _card("When customers order", "Orders by weekday and hour")
        days_n = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        hm = pd.DataFrame([{"Day": days_n[w], "Hour": h, "Orders": n} for (w, h), n in d["heatmap"].items()])
        st.altair_chart(_style(alt.Chart(hm).mark_rect().encode(x=alt.X("Hour:O", title=None), y=alt.Y("Day:N", sort=days_n, title=None),
                                                                color=alt.Color("Orders:Q", scale=alt.Scale(range=["#f4f1ea", INK]), legend=None),
                                                                tooltip=["Day", "Hour", "Orders"]), 260), use_container_width=True)
    with c:
        _card("Payment method")
        pm = pd.DataFrame({"Method": list(d["payment_split"]), "Orders": list(d["payment_split"].values())})
        st.altair_chart(_style(alt.Chart(pm).mark_arc(innerRadius=48, outerRadius=88, stroke="#fff", strokeWidth=2).encode(
            theta="Orders:Q", color=alt.Color("Method:N", scale=alt.Scale(range=[INK, GOLD])), tooltip=["Method", "Orders"]), 260), use_container_width=True)

    a, b = st.columns([1.6, 1], gap="large")
    with a:
        _card("Best-selling pieces", "By revenue")
        st.dataframe(pd.DataFrame([{"Piece": v["name"], "Units": v["units"], "Revenue": v["revenue"]} for _, v in d["top_products"]]), hide_index=True, use_container_width=True,
                     column_config={"Revenue": st.column_config.ProgressColumn(format="₹%d", min_value=0, max_value=max(v["revenue"] for _, v in d["top_products"]))})
    with b:
        _card("Low stock", "Three or fewer left")
        st.dataframe(pd.DataFrame([{"Piece": f"{p['brand']} {p['name']}", "Left": p["stock"]} for p in d["low_stock"]]), hide_index=True, use_container_width=True, height=300,
                     column_config={"Left": st.column_config.ProgressColumn(min_value=0, max_value=3, format="%d")})


def _advance(oid: str, new: str) -> None:
    _, ok = safe(S.orders.set_status, oid, new, ss.user)
    if ok:
        flash("success", f"Order {oid} marked {new}.")


def _orders_tab() -> None:
    f = st.pills("Status", ["All", "Pending Payment", "Placed", "Packed", "Shipped", "Delivered", "Cancelled"], default="All", label_visibility="collapsed") or "All"
    orders = [o for o in S.orders.all(include_synthetic=False) if f == "All" or o["status"] == f]
    if not orders:
        st.info("No orders match. Place an order as a customer to see it here.")
        return
    for o in orders[:40]:
        with st.container(border=True):
            c = st.columns([2.6, 1.2, 1, 1.4, 1.2], vertical_alignment="center")
            c[0].markdown(f"<b>{esc(o['_id'])}</b><div class='muted'>{o['created_at']:%d %b %Y %H:%M} - {esc(o['address']['name'])}, {esc(o['address']['city'])}</div>", unsafe_allow_html=True)
            c[1].markdown(f"<span class='status'>{esc(o['status'])}</span>", unsafe_allow_html=True)
            c[2].markdown(f"<div class='ra serif'>{money(o['total'])}</div>", unsafe_allow_html=True)
            c[3].markdown(f"<div class='muted'>{'COD' if o['payment']['method'] == 'cod' else 'Online'} - {esc(o['payment']['status'])}</div>", unsafe_allow_html=True)
            nxt = STATUS_FLOW.get(o["status"])
            if nxt:
                c[4].button(f"Mark {nxt}", key=f"adv-{o['_id']}", on_click=_advance, args=(o["_id"], nxt), use_container_width=True)


def _product_form(key: str, p: dict | None = None):
    p = p or {}
    c1, c2 = st.columns(2)
    name = c1.text_input("Name", p.get("name", ""), key=f"{key}-name")
    brand = c2.text_input("Brand", p.get("brand", ""), key=f"{key}-brand")
    c3, c4 = st.columns(2)
    category = c3.text_input("Category", p.get("category", ""), key=f"{key}-cat")
    sub = c4.text_input("Subcategory (optional)", p.get("subcategory", ""), key=f"{key}-sub")
    c5, c6 = st.columns(2)
    price = c5.number_input("Price", 0.0, 10_000_000.0, float(p.get("price", 0.0)), 1.0, key=f"{key}-price")
    stock = c6.number_input("Stock", 0, 100_000, int(p.get("stock", 0)), 1, key=f"{key}-stock")
    tags = st.text_input("Tags (comma separated)", ", ".join(p.get("tags", [])), key=f"{key}-tags")
    desc = st.text_area("Description", p.get("description", ""), key=f"{key}-desc")
    up = st.file_uploader("Product photo (JPG / PNG / WebP, up to 5 MB)", type=["jpg", "jpeg", "png", "webp"], key=f"{key}-up")
    return dict(name=name, brand=brand, category=category, subcategory=sub, price=price, stock=stock, image=p.get("image", ""), tags=tags, description=desc), up


def _save(save_fn, data, upload, pid=None):
    saved, ok = safe(save_fn, *([pid] if pid else []), data)
    if ok and upload is not None:
        rel, ok2 = safe(media.save_product_image, saved["_id"], upload.getvalue())
        if ok2:
            safe(S.repo.update, saved["_id"], {**data, "image": rel})
    return saved, ok


def _products_tab() -> None:
    products, ok = safe(S.repo.all)
    if not ok:
        show_flash()
        return
    t1, t2, t3 = st.tabs(["Inventory", "Add product", "Edit / delete"])
    with t1:
        df = pd.DataFrame([{"Photo": media.data_uri(p.get("image"), 96), "ID": p["_id"], "Name": p["name"], "Brand": p["brand"], "Category": p["category"],
                            "Price": p["price"], "Stock": p["stock"]} for p in products])
        st.dataframe(df, hide_index=True, use_container_width=True, height=480,
                     column_config={"Photo": st.column_config.ImageColumn(width="small"), "Price": st.column_config.NumberColumn(format="₹%d"),
                                    "Stock": st.column_config.ProgressColumn(min_value=0, max_value=max(p["stock"] for p in products), format="%d")})
    with t2:
        with st.form("add-product", border=False):
            data, up = _product_form("add")
            if st.form_submit_button("Add product", type="primary"):
                saved, ok = _save(S.repo.add, data, up)
                if ok:
                    flash("success", f"Added {saved['name']} ({saved['_id']}).")
                    st.rerun()
                show_flash()
    with t3:
        label = {p["_id"]: f"{p['_id']} - {p['name']}" for p in products}
        pid = st.selectbox("Product", list(label), format_func=label.get)
        cur = next(p for p in products if p["_id"] == pid)
        with st.form(f"edit-{pid}", border=False):
            data, up = _product_form(f"edit-{pid}", cur)
            if st.form_submit_button("Save changes", type="primary"):
                _, ok = _save(S.repo.update, data, up, pid)
                if ok:
                    flash("success", "Product updated.")
                    st.rerun()
                show_flash()
        confirm = st.checkbox("I understand this permanently deletes the product", key=f"del-ok-{pid}")
        if st.button("Delete product", disabled=not confirm):
            _, ok = safe(S.repo.delete, pid)
            if ok:
                flash("success", "Product deleted.")
                st.rerun()
            show_flash()


def _coupons_tab() -> None:
    rows = S.coupons.all()
    st.dataframe(pd.DataFrame([{"Code": c["_id"], "Offer": c.get("label"), "Type": c["kind"], "Value": c["value"], "Min order": c["min_order"],
                                "Categories": ", ".join(c["categories"]) if c.get("categories") else "All", "Used": c.get("used", 0),
                                "Active": c.get("active", True)} for c in rows]), hide_index=True, use_container_width=True)
    a, b = st.columns(2, gap="large")
    with a:
        with st.form("coupon-new", border=False):
            st.markdown("##### New coupon")
            code = st.text_input("Code", placeholder="MONSOON10")
            kind = st.selectbox("Type", ["percent", "flat"])
            value = st.number_input("Value", 0.0, 100000.0, 10.0)
            c1, c2 = st.columns(2)
            mino = c1.number_input("Minimum order", 0.0, 10_000_000.0, 0.0)
            maxd = c2.number_input("Maximum discount (0 = none)", 0.0, 10_000_000.0, 0.0)
            cats = st.multiselect("Only for categories (empty = all)", S.repo.categories())
            if st.form_submit_button("Create coupon", type="primary"):
                _, ok = safe(S.coupons.create, {"code": code, "kind": kind, "value": value, "min_order": mino, "max_discount": maxd or None,
                                                "categories": cats or None, "label": f"{code}: {value:g}{'%' if kind == 'percent' else ''} off"})
                if ok:
                    flash("success", f"Coupon {code.upper()} created.")
                    st.rerun()
                show_flash()
    with b:
        st.markdown("##### Enable / disable")
        pick = st.selectbox("Coupon", [c["_id"] for c in rows], key="cp_pick")
        cur = next(c for c in rows if c["_id"] == pick)
        st.button("Disable" if cur.get("active", True) else "Enable", key="cp_toggle", on_click=lambda: S.coupons.set_active(pick, not cur.get("active", True)))


def page_admin() -> None:
    st.markdown("<h1>Admin console</h1>", unsafe_allow_html=True)
    show_flash()
    if not is_admin():
        empty_state("Administrators only", "Sign in with an admin account (admin@curio.test) to manage the store.", "Sign in", "Auth", "lock")
        return
    try:
        require_admin(ss.user)
    except AuthError:
        return
    tab = st.segmented_control("Section", ["Dashboard", "Orders", "Products", "Coupons"], default="Dashboard", key="admin_seg",
                               label_visibility="collapsed") or "Dashboard"
    {"Dashboard": _dashboard_tab, "Orders": _orders_tab, "Products": _products_tab, "Coupons": _coupons_tab}[tab]()
