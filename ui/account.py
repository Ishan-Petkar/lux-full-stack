"""Sign-in / register, and the customer account area."""
import streamlit as st

from . import icons
from .checkout import address_form
from .components import empty_state, grid, thumb
from .state import S, esc, flash, go, money, safe, show_flash, ss, uid


# --------------------------------------------------------------------- auth
def _login(email: str, password: str) -> None:
    user, ok = safe(S.users.login, email, password)
    if ok:
        ss.user = user
        flash("success", f"Welcome back, {user['name'].split()[0]}.")
        go("Admin" if user["role"] == "admin" else "Home")


def _register(name: str, email: str, pw: str, pw2: str) -> None:
    if pw != pw2:
        flash("error", "The two passwords do not match.")
        return
    user, ok = safe(S.users.register, name, email, pw)
    if ok:
        ss.user = user
        flash("success", f"Welcome to curio, {user['name'].split()[0]}.")
        go("Home")


def _demo(email: str, password: str) -> None:
    _login(email, password)


def sign_out() -> None:
    ss.user = None
    ss.coupon = None
    go("Home")


def page_auth() -> None:
    if ss.user:
        go("Account")
        st.rerun()
    show_flash()
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        st.markdown("<h1 style='text-align:center'>Welcome to curio.</h1><p class='muted' style='text-align:center'>Sign in to shop, save your wishlist and track orders.</p>",
                    unsafe_allow_html=True)
        with st.container(border=True, key="authbox"):
            t_in, t_reg = st.tabs(["Sign in", "Create account"])
            with t_in:
                with st.form("login", border=False):
                    email = st.text_input("Email", placeholder="you@example.com")
                    pw = st.text_input("Password", type="password")
                    if st.form_submit_button("Sign in", type="primary", use_container_width=True):
                        _login(email, pw)
                        st.rerun()
            with t_reg:
                with st.form("register", border=False):
                    name = st.text_input("Full name", placeholder="Asha Patil")
                    email2 = st.text_input("Email ", placeholder="you@example.com")
                    pw1 = st.text_input("Password ", type="password", help="At least 8 characters with a letter and a number.")
                    pw2 = st.text_input("Confirm password", type="password")
                    if st.form_submit_button("Create account", type="primary", use_container_width=True):
                        _register(name, email2, pw1, pw2)
                        st.rerun()
        st.markdown("<p class='muted' style='text-align:center;margin-top:1rem'>Just looking? Try a demo account</p>", unsafe_allow_html=True)
        a, b = st.columns(2)
        a.button("Demo customer", key="demo", on_click=_demo, args=("demo@example.com", "Demo@1234"), use_container_width=True)
        b.button("Demo admin", key="demo_admin", on_click=_demo, args=("admin@curio.test", "Admin@1234"), use_container_width=True)


# --------------------------------------------------------------------- account
STATUS_CLASS = {"Delivered": "ok", "Cancelled": "bad", "Pending Payment": "warn"}


def _orders_tab() -> None:
    orders, ok = safe(S.orders.history, uid())
    if not ok:
        show_flash()
        return
    if not orders:
        empty_state("No orders yet", "When you place an order it will appear here.", "Start shopping", "Catalog", "box")
        return
    by_id = {p["_id"]: p for p in S.repo.all()}
    for o in orders:
        with st.container(border=True):
            h = st.columns([3, 1.3, 1.1, 1.1], vertical_alignment="center")
            h[0].markdown(f"<b>{esc(o['_id'])}</b><div class='muted'>{o['created_at']:%d %b %Y, %H:%M} UTC - "
                          f"{sum(i['quantity'] for i in o['items'])} item(s)</div>", unsafe_allow_html=True)
            h[1].markdown(f"<span class='status {STATUS_CLASS.get(o['status'], '')}'>{esc(o['status'])}</span>", unsafe_allow_html=True)
            h[2].markdown(f"<div class='ra serif'>{money(o['total'])}</div>", unsafe_allow_html=True)
            h[3].button("Details", key=f"od-{o['_id']}", on_click=go, args=("OrderDetail",), kwargs={"detail_order": o["_id"]}, use_container_width=True)
            st.markdown('<div class="thumbs">' + "".join(thumb(by_id.get(i["product_id"], {"name": i["name"]}), True) for i in o["items"]) + "</div>",
                        unsafe_allow_html=True)


def _wishlist_tab() -> None:
    items = S.wishlist.products_for(uid())
    if not items:
        empty_state("Your wishlist is empty", "Tap the heart on any product to save it here.", "Browse products", "Catalog", "star")
        return
    grid(items, "wl")


def _addr_save() -> None:
    data = {k: ss.get(f"ad_{k}", "") for k in ("label", "name", "phone", "line1", "line2", "city", "state", "pincode")}
    _, ok = safe(S.addresses.add, uid(), data)
    if ok:
        flash("success", "Address saved.")


def _addresses_tab() -> None:
    addrs = S.addresses.list(uid())
    for a in addrs:
        with st.container(border=True):
            c = st.columns([4, 1, 1], vertical_alignment="center")
            c[0].markdown(f"<b>{esc(a['label'])}</b>{' <span class=\"pill ok\">Default</span>' if a['is_default'] else ''}<div class='muted'>{esc(a['name'])} - {esc(a['phone'])}<br>"
                          f"{esc(a['line1'])}{', ' + esc(a['line2']) if a.get('line2') else ''}, {esc(a['city'])}, {esc(a['state'])} {esc(a['pincode'])}</div>", unsafe_allow_html=True)
            if not a["is_default"]:
                c[1].button("Make default", key=f"def-{a['_id']}", on_click=lambda i=a["_id"]: safe(S.addresses.set_default, uid(), i), use_container_width=True)
            c[2].button("Delete", key=f"del-{a['_id']}", on_click=lambda i=a["_id"]: safe(S.addresses.delete, uid(), i), use_container_width=True)
    with st.expander("Add a new address", expanded=not addrs):
        address_form("ad")
        st.button("Save address", key="ad_save", type="primary", on_click=_addr_save)


def _profile_tab() -> None:
    u = ss.user
    a, b = st.columns(2, gap="large")
    with a:
        with st.container(border=True):
            st.markdown("#### Profile")
            st.text_input("Name", value=u["name"], key="pf_name")
            st.text_input("Email", value=u["email"], disabled=True)
            def save():
                new, ok = safe(S.users.update_name, uid(), ss.get("pf_name", ""))
                if ok:
                    ss.user = new
                    flash("success", "Profile updated.")
            st.button("Save profile", key="pf_save", on_click=save, type="primary")
    with b:
        with st.container(border=True):
            st.markdown("#### Change password")
            st.text_input("Current password", type="password", key="pw_old")
            st.text_input("New password", type="password", key="pw_new")
            def change():
                _, ok = safe(S.users.change_password, uid(), ss.get("pw_old", ""), ss.get("pw_new", ""))
                if ok:
                    flash("success", "Password changed.")
            st.button("Update password", key="pw_save", on_click=change)


def page_account() -> None:
    if not ss.user:
        go("Auth")
        st.rerun()
    c1, c2, c3 = st.columns([4, 1.2, 1], vertical_alignment="center")
    c1.markdown(f"<h1 class='h-tight'>Hello, {esc(ss.user['name'].split()[0])}</h1><p class='muted'>{esc(ss.user['email'])}</p>", unsafe_allow_html=True)
    if ss.user["role"] == "admin":
        c2.button("Admin console", key="to_admin", icon=":material/dashboard:", on_click=go, args=("Admin",), use_container_width=True)
    c3.button("Sign out", key="sign_out", icon=":material/logout:", on_click=sign_out, use_container_width=True)
    show_flash()
    tab = st.segmented_control("Section", ["Orders", "Wishlist", "Addresses", "Profile"], default=ss.account_tab, key="acct_seg",
                               label_visibility="collapsed") or "Orders"
    ss.account_tab = tab
    {"Orders": _orders_tab, "Wishlist": _wishlist_tab, "Addresses": _addresses_tab, "Profile": _profile_tab}[tab]()
