"""UI integration tests with Streamlit AppTest (runs the real app script headlessly against mongomock)."""
import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐✅❌]")


@pytest.fixture()
def at():
    t = AppTest.from_file(APP, default_timeout=40)
    t.run()
    assert not t.exception, t.exception
    return t


def press(t, key=None, prefix=None):
    b = t.button(key=key) if key else next(b for b in t.button if (b.key or "").startswith(prefix))
    b.click().run()
    assert not t.exception, t.exception
    return t


def text(t):
    """All rendered markdown with embedded base64 images and the stylesheet removed."""
    raw = " ".join(m.value for m in t.markdown)
    return re.sub(r"<style>.*?</style>", "", re.sub(r"data:image/[a-z]+;base64,[A-Za-z0-9+/=]+", "", raw), flags=re.S)


def sign_in_demo(t):
    press(t, key="acct_btn")
    press(t, key="demo")
    assert t.session_state["user"]["email"] == "demo@example.com"


def open_product(t, label):
    from ui.state import S
    pid = next(p["_id"] for p in S.repo.all() if f"{p['brand']} {p['name']}" == label)
    t.session_state["selected"], t.session_state["view"] = pid, "Product"
    t.run()
    assert not t.exception
    return pid


def test_landing_is_an_editorial_campaign(at):
    body = text(at)
    assert "zmark" in body and "The Collection" in body and "The Watch Edit" in body and "Signature scents" in body
    assert at.button(key="zb-hero") and at.button(key="zb-watch")
    assert "trek" not in body.lower()


def test_no_emoji_and_no_trekking_anywhere(at):
    press(at, key="nav_Shop")
    for t in (text(at), *[b.label for b in at.button]):
        assert not EMOJI.search(t), EMOJI.search(t)
    assert "trek" not in text(at).lower()


def test_landing_cta_opens_collection(at):
    press(at, key="zb-watch")
    assert at.session_state["view"] == "Catalog" and at.session_state["cat"] == "Watches"
    assert any("Watches" in m.value for m in at.markdown)


def test_catalog_index_search_and_empty_state(at):
    press(at, key="nav_Shop")
    assert len([b for b in at.button if (b.key or "").startswith("cat-")]) == 16
    press(at, key="idx_2")                                       # [02] Watches
    assert at.session_state["cat"] == "Watches"
    at.text_input(key="q").set_value("zzzzqqq").run()
    assert "No pieces found" in text(at)
    at.text_input(key="q").set_value("birkin").run()
    assert at.session_state["cat"] == "All" and not at.exception


def test_sign_in_form_and_errors(at):
    press(at, key="acct_btn")
    assert at.session_state["view"] == "Auth"
    at.text_input[1].set_value("demo@example.com")
    at.text_input[2].set_value("wrong")
    next(b for b in at.button if b.label == "Sign in" and "FormSubmitter" in (b.key or "")).click().run()
    assert any("Incorrect email or password" in e.value for e in at.error)
    at.text_input[2].set_value("Demo@1234")
    next(b for b in at.button if b.label == "Sign in" and "FormSubmitter" in (b.key or "")).click().run()
    assert at.session_state["user"]["name"] == "Demo Customer" and at.session_state["view"] == "Home"


def test_register_validation_and_success(at):
    press(at, key="acct_btn")
    forms = [b for b in at.button if b.label == "Create account" and "FormSubmitter" in (b.key or "")]
    at.text_input[3].set_value("Asha Patil")
    at.text_input[4].set_value("asha@example.com")
    at.text_input[5].set_value("weak")
    at.text_input[6].set_value("weak")
    forms[0].click().run()
    assert any("Password must be" in e.value for e in at.error)
    at.text_input[5].set_value("Passw0rd!")
    at.text_input[6].set_value("Passw0rd!")
    next(b for b in at.button if b.label == "Create account" and "FormSubmitter" in (b.key or "")).click().run()
    assert at.session_state["user"]["email"] == "asha@example.com"


def test_sign_out(at):
    sign_in_demo(at)
    press(at, key="acct_btn")
    press(at, key="sign_out")
    assert at.session_state["user"] is None and at.session_state["view"] == "Home"


def test_product_page_has_bundle_similar_and_reviews(at):
    sign_in_demo(at)
    from ui.state import S
    S.cart.clear("U-demo0001")
    pid = open_product(at, "Rolex Submariner")
    body = text(at)
    assert "Frequently bought together" in body and "You may also like" in body and "Reviews" in body and "Switzerland" in body
    press(at, key="fbt_add")
    assert len(S.cart.view("U-demo0001")["lines"]) >= 2


def test_quick_add_and_add_require_sign_in(at):
    press(at, key="nav_Shop")
    next(b for b in at.button if (b.key or "").startswith("qa-")).click().run()
    assert at.session_state["view"] == "Auth"


def test_cod_checkout_end_to_end(at):
    sign_in_demo(at)
    from ui.state import S
    S.cart.clear("U-demo0001")
    S.addresses.add("U-demo0001", dict(name="Demo Customer", phone="9876543210", line1="12 Baner Road", city="Pune", state="Maharashtra", pincode="411045"))
    pid = open_product(at, "Smythson Soho Notebook")
    press(at, key=f"add-{pid}")
    press(at, key="bag")
    assert "Order summary" in text(at)
    press(at, key="to_checkout")
    assert "Delivery address" in text(at)
    at.radio[-1].set_value("cod").run()
    press(at, key="place")
    assert at.session_state["view"] == "Confirmation" and "order is confirmed" in text(at) and "pay on delivery" in text(at)


def test_admin_requires_admin_role(at):
    press(at, key="nav_Shop")
    at.session_state["view"] = "Admin"
    at.run()
    assert "Administrators only" in text(at)
    press(at, key="acct_btn")
    press(at, key="demo_admin")
    assert at.session_state["view"] == "Admin" and "Admin console" in text(at)


def test_help_lists_demo_payment_values(at):
    press(at, key="nav_Help")
    assert "success@razorpay" in text(at) and "4111 1111 1111 1111" in text(at)
