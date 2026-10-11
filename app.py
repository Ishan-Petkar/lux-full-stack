"""curio - AI-Based Product Recommendation System · Streamlit storefront.

Run:  streamlit run app.py     (or ./start.sh)
"""
import streamlit as st

st.set_page_config(page_title="CURIO | Luxury", page_icon=":material/diamond:", layout="wide", initial_sidebar_state="collapsed")

from shop.theme import CSS  # noqa: E402

st.markdown(CSS, unsafe_allow_html=True)

from ui.account import page_account, page_auth  # noqa: E402
from ui.admin import page_admin  # noqa: E402
from ui.checkout import page_cart, page_checkout, page_confirmation, page_order_detail  # noqa: E402
from ui.header import footer, header  # noqa: E402
from ui.help_page import page_help  # noqa: E402
from ui.landing import page_home  # noqa: E402
from ui.shop_pages import page_catalog, page_product  # noqa: E402
from ui.state import S, init_state, ss  # noqa: E402

init_state()

PAGES = {"Home": page_home, "Catalog": page_catalog, "Product": page_product, "Cart": page_cart, "Checkout": page_checkout,
         "Confirmation": page_confirmation, "OrderDetail": page_order_detail, "Account": page_account, "Auth": page_auth,
         "Admin": page_admin, "Help": page_help}

S.orders.expire_pending()          # release stock held by abandoned online payments
header()
with st.container(key=f"page-{ss.view}"):      # a new key per page => the CSS entrance animation replays on every navigation
    PAGES.get(ss.view, page_home)()
footer()
