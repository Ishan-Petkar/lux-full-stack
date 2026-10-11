"""Shared state, service wiring and small helpers for every page."""
import html
from types import SimpleNamespace

import streamlit as st

from shop import config, media
from shop.addresses import AddressService
from shop.bundles import BundleService
from shop.cart import CartService
from shop.catalog import ProductRepository
from shop.coupons import CouponService
from shop.db import connect
from shop.errors import ShopError
from shop.orders import OrderService
from shop.payments import PaymentService
from shop.recommender import RecommenderService
from shop.reviews import ReviewService
from shop.seed_data import seed_if_empty
from shop.users import UserRepository
from shop.wishlist import WishlistService

PAGE_SIZE = 16
CAT_LABEL = {"Leather & Writing": "Leather & writing"}


@st.cache_resource(show_spinner="Connecting to the database...")
def services() -> SimpleNamespace:
    db, backend = connect()
    seed_if_empty(db)
    repo = ProductRepository(db)
    coupons, payments = CouponService(db), PaymentService(db)
    return SimpleNamespace(db=db, backend=backend, repo=repo, users=UserRepository(db), cart=CartService(db), coupons=coupons,
                           payments=payments, orders=OrderService(db, coupons, payments), reco=RecommenderService(repo),
                           bundles=BundleService(db), wishlist=WishlistService(db), reviews=ReviewService(db),
                           addresses=AddressService(db))


S = services()
ss = st.session_state
DEFAULTS = {"view": "Home", "user": None, "selected": None, "flash": [], "shown": PAGE_SIZE, "filter_sig": None, "recent": [],
            "order_id": None, "coupon": None, "ship": "standard", "pay_method": "razorpay", "addr_id": None, "pay": None,
            "detail_order": None, "account_tab": "Orders", "cat": "All", "sub": "All"}


def init_state() -> None:
    """Call at the top of EVERY script run: modules are cached across sessions, so defaults must not be set at import time."""
    for k, v in DEFAULTS.items():
        if k not in ss:
            ss[k] = list(v) if isinstance(v, list) else v


def flash(kind: str, msg: str) -> None:
    ss.flash.append((kind, msg))


def show_flash() -> None:
    for kind, msg in ss.flash:
        if kind in ("success", "info"):
            st.toast(msg, icon=":material/check_circle:" if kind == "success" else ":material/info:")
        elif kind == "warning":
            st.warning(msg)
        else:
            st.error(msg)
    ss.flash = []


def money(x: float) -> str:
    return f"{config.CURRENCY}{x:,.0f}" if float(x).is_integer() else f"{config.CURRENCY}{x:,.2f}"


def esc(x) -> str:
    return html.escape(str(x if x is not None else ""))


def go(view: str, selected: str | None = None, **extra) -> None:
    ss.view = view
    if selected is not None:
        ss.selected = selected
        ss.recent = [selected] + [i for i in ss.recent if i != selected][:7]
    for k, v in extra.items():
        ss[k] = v


def safe(fn, *a, **kw):
    """Run a service call; show friendly errors instead of stack traces."""
    try:
        return fn(*a, **kw), True
    except ShopError as exc:
        flash("error", str(exc))
    except Exception:
        flash("error", "Something went wrong. Please try again.")
    return None, False


def is_admin() -> bool:
    return bool(ss.user and ss.user.get("role") == "admin")


def uid() -> str | None:
    return ss.user["_id"] if ss.user else None


def img_html(p: dict, size: int = 520) -> str:
    uri = media.data_uri(p.get("image"), size)
    if uri:
        return f'<img src="{uri}" alt="{esc(p.get("name"))}" loading="lazy">'
    initial = esc((p.get("brand") or p.get("name") or "?")[:1])
    return f'<div class="ph"><span>{initial}</span></div>'
