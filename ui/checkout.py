"""Bag, checkout, demo-Razorpay payment dialog, order tracking and confirmation."""
from datetime import date, timedelta

import streamlit as st

from shop import config, pricing
from shop.errors import PaymentError, ShopError
from shop.invoice import invoice_html
from shop.payments import BANKS
from . import icons
from .components import empty_state, thumb
from .state import S, esc, flash, go, money, safe, show_flash, ss, uid


# --------------------------------------------------------------------- shared price block
def _lines_for_coupon(view: dict) -> list[dict]:
    return [{"category": l["product"]["category"], "line_total": l["line_total"]} for l in view["lines"]]


def current_pricing(view: dict) -> dict:
    """Quote for the bag with the applied coupon and chosen delivery (drops an invalid coupon with a warning)."""
    discount, code = 0.0, None
    if ss.coupon:
        try:
            c = S.coupons.evaluate(ss.coupon, _lines_for_coupon(view))
            discount, code = c["discount"], c["code"]
        except ShopError as exc:
            flash("warning", f"Coupon removed: {exc}")
            ss.coupon = None
    q = pricing.quote(view["total"], discount, ss.ship)
    q["coupon_code"] = code
    return q


def price_rows(q: dict) -> str:
    rows = [f"<div class='summary-row'><span>Subtotal</span><span>{money(q['subtotal'])}</span></div>"]
    if q["discount"]:
        rows.append(f"<div class='summary-row ok'><span>Discount ({esc(q['coupon_code'])})</span><span>-{money(q['discount'])}</span></div>")
    rows.append(f"<div class='summary-row'><span>Delivery</span><span>{'Free' if q['shipping'] == 0 else money(q['shipping'])}</span></div>")
    rows.append(f"<div class='summary-row muted'><span>Includes GST ({int(config.GST_RATE * 100)}%)</span><span>{money(q['gst_included'])}</span></div>")
    rows.append(f"<div class='summary-total'><span>Total</span><span>{money(q['total'])}</span></div>")
    return "".join(rows)


def _apply_coupon(code: str) -> None:
    code = (code or "").strip()
    if not code:
        return
    v, ok = safe(S.cart.view, uid())
    if not ok:
        return
    try:
        c = S.coupons.evaluate(code, _lines_for_coupon(v))
        ss.coupon = c["code"]
        flash("success", f"{c['code']} applied: {c['label']}.")
    except ShopError as exc:
        flash("error", str(exc))


def _remove_coupon() -> None:
    ss.coupon = None


def coupon_box() -> None:
    if ss.coupon:
        a, b = st.columns([3, 1], vertical_alignment="center")
        a.markdown(f"<span class='pill ok'>{esc(ss.coupon)} applied</span>", unsafe_allow_html=True)
        b.button("Remove", key="coupon_rm", on_click=_remove_coupon, type="tertiary")
    else:
        with st.form("coupon_form", border=False, clear_on_submit=True):
            a, b = st.columns([2.2, 1], vertical_alignment="bottom")
            code = a.text_input("Coupon code", placeholder="e.g. WELCOME10", label_visibility="collapsed")
            if b.form_submit_button("Apply", use_container_width=True):
                _apply_coupon(code)
                st.rerun()


# --------------------------------------------------------------------- bag
def _set_qty(pid: str, key: str) -> None:
    safe(S.cart.set_quantity, uid(), pid, ss[key])


def _remove(pid: str) -> None:
    safe(S.cart.remove, uid(), pid)
    flash("info", "Item removed from your bag.")


def page_cart() -> None:
    st.markdown("<h1>Your bag</h1>", unsafe_allow_html=True)
    show_flash()
    if not ss.user:
        empty_state("Sign in to see your bag", "Your bag is saved to your account.", "Sign in", "Auth", "lock")
        return
    view, ok = safe(S.cart.view, uid())
    if not ok:
        show_flash()
        return
    if not view["lines"]:
        empty_state("Your bag is empty", "Find something you like and it will show up here.", "Start shopping", "Catalog", "box")
        return
    for msg in view["issues"]:
        st.warning(msg)
    left, right = st.columns([2.2, 1], gap="large")
    with left:
        for ln in view["lines"]:
            p = ln["product"]
            with st.container(border=True):
                c = st.columns([0.9, 3.2, 1.3, 1.2, 0.5], vertical_alignment="center")
                c[0].markdown(thumb(p), unsafe_allow_html=True)
                c[1].markdown(f"<div class='lname'>{esc(p['name'])}</div><div class='lmeta'>{esc(p['brand'])} · {money(ln['unit_price'])} each</div>",
                              unsafe_allow_html=True)
                key = f"cartqty-{p['_id']}"
                ss[key] = min(max(ln["quantity"], 1), config.MAX_LINE_QTY)
                c[2].number_input("Quantity", 1, config.MAX_LINE_QTY, key=key, label_visibility="collapsed", on_change=_set_qty, args=(p["_id"], key))
                c[3].markdown(f"<div class='ra strong'>{money(ln['line_total'])}</div>", unsafe_allow_html=True)
                c[4].button("", key=f"rm-{p['_id']}", icon=":material/close:", on_click=_remove, args=(p["_id"],), help="Remove", type="tertiary")
    with right:
        q = current_pricing(view)
        with st.container(border=True, key="summary"):
            st.markdown("<h3 style='margin-top:0'>Order summary</h3>", unsafe_allow_html=True)
            coupon_box()
            st.markdown(price_rows(q), unsafe_allow_html=True)
            st.button("Checkout", key="to_checkout", type="primary", use_container_width=True, icon=":material/lock:",
                      on_click=go, args=("Checkout",), disabled=bool(view["issues"]))
            if q["shipping"] and q["subtotal"] - q["discount"] < config.FREE_SHIPPING_MIN:
                st.caption(f"Add {money(config.FREE_SHIPPING_MIN - (q['subtotal'] - q['discount']))} more for free delivery.")


# --------------------------------------------------------------------- checkout
def _place_order() -> None:
    method = ss.get("pay_method", "razorpay")
    o, ok = safe(S.orders.create, uid(), ss.addr_id, ss.ship, ss.coupon, method)
    if not ok:
        return
    ss.coupon = None
    if method == "cod":
        ss.order_id = o["_id"]
        go("Confirmation")
    else:
        ss.detail_order, ss.pay_open = o["_id"], True
        go("OrderDetail")


def _add_address() -> None:
    data = {k: ss.get(f"na_{k}", "") for k in ("label", "name", "phone", "line1", "line2", "city", "state", "pincode")}
    a, ok = safe(S.addresses.add, uid(), data)
    if ok:
        ss.addr_id = a["_id"]
        flash("success", "Address saved.")


def address_form(prefix: str = "na") -> None:
    c1, c2 = st.columns(2)
    c1.text_input("Full name", key=f"{prefix}_name", value=ss.user["name"] if ss.user else "")
    c2.text_input("Mobile number", key=f"{prefix}_phone", placeholder="98765 43210", max_chars=14)
    st.text_input("Address line 1", key=f"{prefix}_line1", placeholder="Flat / house, street")
    st.text_input("Address line 2 (optional)", key=f"{prefix}_line2")
    c3, c4, c5, c6 = st.columns([1.2, 1.2, 1, 1])
    c3.text_input("City", key=f"{prefix}_city")
    c4.text_input("State", key=f"{prefix}_state")
    c5.text_input("PIN code", key=f"{prefix}_pincode", max_chars=6)
    c6.text_input("Label", key=f"{prefix}_label", placeholder="Home / Work")


def page_checkout() -> None:
    st.markdown("<h1>Checkout</h1>", unsafe_allow_html=True)
    show_flash()
    if not ss.user:
        empty_state("Sign in to check out", "", "Sign in", "Auth", "lock")
        return
    view, ok = safe(S.cart.view, uid())
    if not ok or not view["lines"]:
        show_flash()
        empty_state("Your bag is empty", "Add something before checking out.", "Start shopping", "Catalog", "box")
        return
    for msg in view["issues"]:
        st.warning(msg)
    addrs = S.addresses.list(uid())
    if addrs and ss.addr_id not in {a["_id"] for a in addrs}:
        ss.addr_id = addrs[0]["_id"]
    left, right = st.columns([2, 1], gap="large")
    with left:
        with st.container(border=True):
            st.markdown("<div class='step'><span>1</span> Delivery address</div>", unsafe_allow_html=True)
            if addrs:
                labels = {a["_id"]: f"{a['label']} - {a['name']}, {a['line1']}, {a['city']} {a['pincode']}" for a in addrs}
                ss.addr_id = st.radio("Address", list(labels), format_func=labels.get, index=list(labels).index(ss.addr_id),
                                      label_visibility="collapsed")
            with st.expander("Add a new address", expanded=not addrs):
                address_form()
                st.button("Save address", key="save_addr", on_click=_add_address)
        q0 = pricing.quote(view["total"], 0, "standard")
        pin = next((a["pincode"] for a in addrs if a["_id"] == ss.addr_id), None)
        with st.container(border=True):
            st.markdown("<div class='step'><span>2</span> Delivery method</div>", unsafe_allow_html=True)
            q_now = current_pricing(view)
            opts = {o["key"]: o for o in pricing.shipping_options(q_now["subtotal"] - q_now["discount"])}
            def _lbl(k):
                lo, hi = pricing.eta_days(pin, k)
                f = lambda n: (date.today() + timedelta(days=n)).strftime("%d %b")
                return f"{opts[k]['label']} - {'Free' if opts[k]['fee'] == 0 else money(opts[k]['fee'])} - arrives {f(lo)} to {f(hi)}"
            ss.ship = st.radio("Delivery", list(opts), format_func=_lbl, index=list(opts).index(ss.ship), label_visibility="collapsed")
        with st.container(border=True):
            st.markdown("<div class='step'><span>3</span> Payment</div>", unsafe_allow_html=True)
            ss.pay_method = st.radio("Payment", ["razorpay", "cod"], label_visibility="collapsed",
                                     format_func=lambda m: "Pay online - UPI, card or netbanking (Razorpay, demo mode)" if m == "razorpay"
                                     else "Cash on delivery (orders up to 50,000)",
                                     index=["razorpay", "cod"].index(ss.get("pay_method", "razorpay")))
            if ss.pay_method == "razorpay":
                st.caption("You will pay in a secure checkout window. Demo mode: no real money moves; test values are listed in the Help centre.")
    with right:
        q = current_pricing(view)
        with st.container(border=True, key="summary"):
            st.markdown("<h3 style='margin-top:0'>Order summary</h3>", unsafe_allow_html=True)
            st.markdown('<div class="thumbs">' + "".join(thumb(l["product"], True) for l in view["lines"]) + "</div>", unsafe_allow_html=True)
            coupon_box()
            st.markdown(price_rows(q), unsafe_allow_html=True)
            label = f"Pay {money(q['total'])}" if ss.pay_method == "razorpay" else f"Place order - {money(q['total'])}"
            st.button(label, key="place", type="primary", use_container_width=True, icon=":material/lock:", on_click=_place_order,
                      disabled=bool(view["issues"]) or not addrs)
            if not addrs:
                st.caption("Add a delivery address to continue.")
            st.button("Back to bag", key="back_bag", on_click=go, args=("Cart",), type="tertiary")


# --------------------------------------------------------------------- demo Razorpay checkout dialog
def _pay_success(order_id: str, result: dict) -> None:
    o, ok = safe(S.orders.confirm_payment, order_id, uid(), result)
    if ok:
        ss.pay = None
        ss.order_id = order_id
        go("Confirmation")
        st.rerun()


@st.dialog("Secure checkout", width="large")
def pay_dialog(order_id: str) -> None:
    order, ok = safe(S.orders.get, order_id, uid())
    if not ok or order["status"] != "Pending Payment":
        show_flash()
        return
    pay = ss.pay if ss.pay and ss.pay.get("order_id") == order_id else None
    if not pay:
        rz, ok = safe(S.orders.start_payment, order_id, uid())
        if not ok:
            show_flash()
            return
        pay = ss.pay = {"order_id": order_id, "rz": rz, "stage": "form", "error": None}
    rz = pay["rz"]
    st.markdown(f'<div class="rz-head"><div><b>{esc(config.MERCHANT_NAME)}</b><div class="muted">Order {esc(order_id)}</div></div>'
                f'<div class="rz-amt">{money(order["total"])}<span class="pill dark">TEST MODE</span></div></div>', unsafe_allow_html=True)
    st.caption("Demo gateway modelled on Razorpay test mode. No real money moves and no card is stored.")
    if pay.get("error"):
        st.error(pay["error"])

    if pay["stage"] == "bank":
        st.markdown('<div class="bank"><b>Test bank authentication</b><div class="muted">Mirrors the Razorpay test bank page. Choose the outcome.</div></div>',
                    unsafe_allow_html=True)
        a, b = st.columns(2)
        if a.button("Success", key="bank_ok", type="primary", use_container_width=True):
            try:
                res = S.payments.bank_result(rz["id"], True)
                _pay_success(order_id, res)
            except ShopError as exc:
                pay["error"], pay["stage"] = str(exc), "form"
                st.rerun(scope="fragment")
        if b.button("Failure", key="bank_fail", use_container_width=True):
            try:
                S.payments.bank_result(rz["id"], False)
            except ShopError as exc:
                S.orders.payment_failed(order_id, str(exc))
                pay["error"], pay["stage"] = str(exc), "form"
                st.rerun(scope="fragment")
        return

    tabs = st.tabs(["UPI", "Card", "Netbanking"])

    def attempt(method: str, details: dict) -> None:
        try:
            res = S.payments.authorize(rz["id"], method, details)
            pay["error"] = None
            if res["next"] == "paid":
                _pay_success(order_id, res["payment"])
            else:
                pay["stage"] = "bank"
                st.rerun(scope="fragment")
        except ShopError as exc:
            S.orders.payment_failed(order_id, str(exc))
            pay["error"] = str(exc)
            st.rerun(scope="fragment")

    with tabs[0]:
        with st.form("upi", border=False):
            vpa = st.text_input("UPI ID", placeholder="success@razorpay")
            st.caption("Demo: success@razorpay pays, failure@razorpay fails.")
            if st.form_submit_button(f"Pay {money(order['total'])}", type="primary", use_container_width=True):
                attempt("upi", {"vpa": vpa})
    with tabs[1]:
        with st.form("card", border=False):
            num = st.text_input("Card number", placeholder="4111 1111 1111 1111", max_chars=23)
            c1, c2 = st.columns(2)
            exp = c1.text_input("Expiry (MM/YY)", placeholder="12/35", max_chars=5)
            cvv = c2.text_input("CVV", type="password", max_chars=4)
            holder = st.text_input("Name on card", value=ss.user["name"])
            st.caption("Demo test cards: 4111 1111 1111 1111, 5267 3181 8797 5449, 5104 0155 5555 5558.")
            if st.form_submit_button(f"Pay {money(order['total'])}", type="primary", use_container_width=True):
                attempt("card", {"number": num, "expiry": exp, "cvv": cvv, "holder": holder})
    with tabs[2]:
        with st.form("nb", border=False):
            bank = st.selectbox("Choose your bank", BANKS)
            if st.form_submit_button(f"Continue to bank - {money(order['total'])}", type="primary", use_container_width=True):
                attempt("netbanking", {"bank": bank})


# --------------------------------------------------------------------- order detail / tracking
STEPS = ["Placed", "Packed", "Shipped", "Delivered"]


def timeline_html(o: dict) -> str:
    if o["status"] == "Cancelled":
        return "<div class='tl'><div class='tl-step bad on'><i></i><span>Cancelled</span></div></div>"
    if o["status"] == "Pending Payment":
        return "<div class='tl'><div class='tl-step warn on'><i></i><span>Awaiting payment</span></div></div>"
    idx = STEPS.index(o["status"])
    done = {t["status"]: t["at"] for t in o["timeline"]}
    out = []
    for i, s in enumerate(STEPS):
        cls = "on" if i <= idx else ""
        when = f"<small>{done[s]:%d %b, %H:%M}</small>" if s in done else ""
        out.append(f"<div class='tl-step {cls}'><i>{icons.icon('check', 12, 3) if i <= idx else ''}</i><span>{s}</span>{when}</div>")
    return "<div class='tl'>" + "".join(out) + "</div>"


def page_order_detail() -> None:
    oid = ss.detail_order
    o, ok = safe(S.orders.get, oid, uid()) if oid and ss.user else (None, False)
    if not ok:
        show_flash()
        empty_state("Order not found", "", "My orders", "Account", "box")
        return
    st.button("All orders", key="back_orders", icon=":material/arrow_back:", on_click=go, args=("Account",), kwargs={"account_tab": "Orders"}, type="tertiary")
    show_flash()
    if ss.pop("pay_open", False) and o["status"] == "Pending Payment":
        pay_dialog(oid)
    st.markdown(f"<h1>Order {esc(o['_id'])}</h1><p class='muted'>Placed {o['created_at']:%d %b %Y, %H:%M} UTC</p>", unsafe_allow_html=True)
    st.markdown(timeline_html(o), unsafe_allow_html=True)
    left, right = st.columns([1.6, 1], gap="large")
    by_id = {p["_id"]: p for p in S.repo.all()}
    with left:
        with st.container(border=True):
            for it in o["items"]:
                p = by_id.get(it["product_id"], {"name": it["name"], "image": it.get("image", ""), "brand": it.get("brand", "")})
                c = st.columns([0.8, 3, 1.2], vertical_alignment="center")
                c[0].markdown(thumb(p), unsafe_allow_html=True)
                c[1].markdown(f"<div class='lname'>{esc(it['name'])}</div><div class='lmeta'>Qty {it['quantity']} x {money(it['unit_price'])}</div>", unsafe_allow_html=True)
                c[2].markdown(f"<div class='ra strong'>{money(it['line_total'])}</div>", unsafe_allow_html=True)
        with st.expander("Activity", expanded=False):
            for t in reversed(o["timeline"]):
                st.markdown(f"**{esc(t['status'])}** - {t['at']:%d %b %Y, %H:%M} UTC  \n<span class='muted'>{esc(t.get('note', ''))}</span>", unsafe_allow_html=True)
    with right:
        a = o["address"]
        pay = o["payment"]
        how = "Cash on delivery" if pay["method"] == "cod" else (f"{pay.get('network') or ''} card ending {pay['last4']}" if pay.get("last4")
              else (pay.get("bank") or ("UPI" if pay.get("method_used") == "upi" else "Online payment")))
        with st.container(border=True):
            st.markdown(f"<h3 style='margin-top:0'>Summary</h3>{price_rows({**o['pricing'], 'coupon_code': o['pricing'].get('coupon_code')})}"
                        f"<div class='muted' style='margin-top:.6rem'>Payment: {esc(how)} - <b>{esc(pay['status'])}</b></div>"
                        f"<div class='muted' style='margin-top:.6rem'>Ship to<br><b>{esc(a['name'])}</b><br>{esc(a['line1'])}"
                        f"{', ' + esc(a['line2']) if a.get('line2') else ''}<br>{esc(a['city'])}, {esc(a['state'])} {esc(a['pincode'])}</div>", unsafe_allow_html=True)
            if o["status"] == "Pending Payment":
                st.button("Pay now", key="paynow", type="primary", icon=":material/lock:", use_container_width=True,
                          on_click=lambda: ss.__setitem__("pay_open", True))
            if o["status"] in ("Pending Payment", "Placed", "Packed"):
                st.button("Cancel order", key="cancel_order", use_container_width=True, on_click=_cancel, args=(oid,))
            st.download_button("Download invoice", invoice_html(o), file_name=f"invoice-{oid}.html", mime="text/html",
                               icon=":material/download:", use_container_width=True, key="inv")
            st.button("Buy again", key="buy_again", use_container_width=True, icon=":material/replay:", on_click=_buy_again, args=(oid,))


def _cancel(oid: str) -> None:
    o, ok = safe(S.orders.cancel, oid, uid())
    if ok:
        flash("success", "Order cancelled." + (" Your refund has been initiated." if o["payment"]["status"] == "refunded" else ""))
        ss.pay = None


def _buy_again(oid: str) -> None:
    o, ok = safe(S.orders.get, oid, uid())
    if ok:
        n = sum(1 for it in o["items"] if safe(S.cart.add, uid(), it["product_id"], it["quantity"])[1])
        flash("success" if n else "warning", f"Added {n} item(s) to your bag." if n else "Those items are unavailable right now.")
        go("Cart")


# --------------------------------------------------------------------- confirmation
def page_confirmation() -> None:
    o, ok = safe(S.orders.get, ss.order_id, uid()) if ss.order_id and ss.user else (None, False)
    if not ok:
        go("Account", account_tab="Orders")
        st.rerun()
    st.markdown(f'<div class="tick">{icons.icon("check", 34, 2.4)}</div>', unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center'>Thank you - your order is confirmed</h1>", unsafe_allow_html=True)
    cod = o["payment"]["method"] == "cod"
    st.markdown(f"<p style='text-align:center' class='muted'>Order <b>{esc(o['_id'])}</b> - {o['created_at']:%d %b %Y, %H:%M} UTC"
                f"{' - pay on delivery' if cod else ' - payment received'}</p>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        by_id = {p["_id"]: p for p in S.repo.all()}
        with st.container(border=True):
            for it in o["items"]:
                p = by_id.get(it["product_id"], {"name": it["name"], "image": it.get("image", "")})
                c = st.columns([0.8, 3, 1.2], vertical_alignment="center")
                c[0].markdown(thumb(p), unsafe_allow_html=True)
                c[1].markdown(f"<div class='lname'>{esc(it['name'])}</div><div class='lmeta'>Qty {it['quantity']} x {money(it['unit_price'])}</div>", unsafe_allow_html=True)
                c[2].markdown(f"<div class='ra strong'>{money(it['line_total'])}</div>", unsafe_allow_html=True)
            st.markdown(price_rows({**o["pricing"], "coupon_code": o["pricing"].get("coupon_code")}), unsafe_allow_html=True)
        lo, hi = pricing.eta_days(o["address"]["pincode"], o["pricing"]["shipping_method"])
        f = lambda n: (date.today() + timedelta(days=n)).strftime("%a, %d %b")
        st.markdown(f"<p class='muted' style='text-align:center'>Estimated delivery {f(lo)} - {f(hi)} (illustrative)</p>", unsafe_allow_html=True)
        b1, b2, b3 = st.columns(3)
        b1.button("Track order", key="track", on_click=go, args=("OrderDetail",), kwargs={"detail_order": o["_id"]}, type="primary", use_container_width=True)
        b2.button("Continue shopping", key="cs", on_click=go, args=("Catalog",), use_container_width=True)
        b3.download_button("Invoice", invoice_html(o), file_name=f"invoice-{o['_id']}.html", mime="text/html", use_container_width=True, key="inv_c")
