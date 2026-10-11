"""Help centre: delivery, payments (demo), returns and the demo credentials."""
import streamlit as st

from shop import config
from shop.payments import BANKS, TEST_CARDS
from .state import esc, ss


def page_help() -> None:
    st.markdown("<h1>Help centre</h1>", unsafe_allow_html=True)
    a, b = st.columns([1.2, 1], gap="large")
    with a:
        with st.expander("Delivery", expanded=True):
            st.write(f"Insured standard delivery is complimentary above {config.CURRENCY}{config.FREE_SHIPPING_MIN:,} and {config.CURRENCY}{config.SHIPPING['standard']['fee']} below it "
                     f"(3-5 days). Priority insured courier costs {config.CURRENCY}{config.SHIPPING['express']['fee']} (1-2 days). Remote PIN codes add two days. "
                     "Delivery estimates are illustrative; nothing is shipped in this demo.")
        with st.expander("Cancellations and refunds"):
            st.write("Orders can be cancelled until they are shipped. Stock is released immediately. Paid orders are refunded to the original "
                     "payment method (simulated). Unpaid online orders are cancelled automatically after "
                     f"{config.PENDING_PAYMENT_MINUTES} minutes.")
        with st.expander("Prices, GST and coupons"):
            st.write(f"All prices include GST at {int(config.GST_RATE * 100)}%; the invoice shows the tax portion. Try coupons WELCOME10, FLAT5000, "
                     "TIMELESS8 (watches and jewellery) and SCENT15 (fragrance).")
        with st.expander("How recommendations work"):
            st.write("'You may also like' compares product descriptions with TF-IDF and cosine similarity. 'Frequently bought together' uses "
                     "market-basket statistics (confidence and lift) over past orders. The starting history is synthetic and is clearly disclosed in the docs.")
    with b:
        with st.container(border=True):
            st.markdown("#### Demo credentials")
            st.markdown("**Customer** demo@example.com / Demo@1234  \n**Admin** admin@curio.test / Admin@1234")
            st.markdown("#### Demo payments (Razorpay test mode)")
            st.markdown("No real money moves. Use these test values at checkout:")
            st.markdown("- **UPI:** `success@razorpay` pays, `failure@razorpay` fails\n"
                        "- **Cards:** " + ", ".join(f"`{c[:4]} {c[4:8]} {c[8:12]} {c[12:]}`" for c in sorted(TEST_CARDS)) +
                        " with any future expiry and any CVV; then choose Success or Failure on the bank page\n"
                        f"- **Netbanking:** any bank ({', '.join(BANKS[:3])} ...), then Success or Failure\n"
                        "- **Cash on delivery** is available up to 50,000")
