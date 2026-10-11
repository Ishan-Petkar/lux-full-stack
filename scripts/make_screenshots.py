"""End-to-end browser run of the storefront that also captures the documentation screenshots into docs/screenshots.

Usage:  ./start.sh   then   python scripts/make_screenshots.py [http://localhost:8501]
It places real demo orders (UPI, a failed payment, card + bank page, cash on delivery, a cancellation) in whatever database the app uses,
and raises if any step misbehaves, so a clean run is also an end-to-end test of the payment flow.
"""
import os
import re
import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
for old in OUT.glob("*.png"):
    old.unlink()
sys.path.insert(0, str(ROOT))
os.environ.setdefault("USE_MOCK_DB", "false")
from shop.db import connect  # noqa: E402

connect()[0].carts.update_one({"_id": "U-demo0001"}, {"$set": {"items": []}}, upsert=True)


def settle(p, ms=1300):
    p.wait_for_timeout(ms)


def shot(p, name):
    settle(p, 900)
    p.screenshot(path=str(OUT / name))
    print("saved", name)


def btn(p, text, nth=0, exact=True):
    return p.get_by_role("button", name=re.compile(r"(^|\s)" + re.escape(text) + ("$" if exact else ""))).nth(nth)


def scroll(p, dy):
    p.evaluate(f"document.querySelector('[data-testid=\"stMain\"]').scrollBy(0,{dy})")
    settle(p, 1500)


def search(p, text):
    box = p.get_by_placeholder("Search")
    box.fill(text); box.press("Enter"); settle(p, 2600)


def open_piece(p, text):
    search(p, text)
    btn(p, "View").click()
    p.get_by_text("Frequently bought together").or_(p.get_by_text("You may also like")).first.wait_for(timeout=25000)
    settle(p, 1800)


def fresh(br, w=1440, h=900):
    p = br.new_page(viewport={"width": w, "height": h})
    p.goto(URL)
    btn(p, "Bag (", exact=False).wait_for(timeout=40000)
    settle(p, 3000)
    return p


def dialog(p):
    d = p.get_by_role("dialog")
    d.get_by_text("Secure checkout").wait_for(timeout=20000)
    settle(p, 1200)
    return d


with sync_playwright() as pw:
    br = pw.chromium.launch(channel="chrome", headless=True)
    page = fresh(br)
    shot(page, "01_landing_hero.png")
    for i, name in enumerate(("02_landing_wall.png", "03_landing_watch.png", "04_landing_bags_jewellery.png", "05_landing_fragrance.png",
                              "06_landing_new_arrivals.png", "07_landing_atelier.png")):
        scroll(page, 880 if i else 900)
        shot(page, name)
    scroll(page, -9000)

    btn(page, "Discover").click(); settle(page, 3000); shot(page, "08_collection.png")
    page.get_by_role("button", name=re.compile(r"\[02\]")).click(); settle(page, 2600); shot(page, "09_watches_index.png")
    btn(page, "Filters").click(); settle(page, 900); shot(page, "10_filters.png"); page.keyboard.press("Escape")

    open_piece(page, "Rolex Submariner"); shot(page, "11_product_page.png")
    scroll(page, 900); shot(page, "12_frequently_bought_together.png")
    scroll(page, 800); shot(page, "13_similar_and_reviews.png")

    btn(page, "Log in").click(); settle(page, 2200)
    page.get_by_label("Email").first.fill("demo@example.com"); page.get_by_label("Password").first.fill("wrong")
    page.get_by_label("Password").first.press("Enter"); settle(page, 1800)
    expect(page.get_by_text("Incorrect email or password")).to_be_visible(); shot(page, "14_log_in_error.png")
    page.get_by_label("Password").first.fill("Demo@1234"); page.get_by_label("Password").first.press("Enter"); settle(page, 2600)
    expect(btn(page, "Demo")).to_be_visible()

    open_piece(page, "Rolex Submariner")
    btn(page, "Add all to bag").click(); settle(page, 1800)
    btn(page, "Bag (", exact=False).click(); page.get_by_text("Order summary").wait_for(); settle(page, 1800)
    page.get_by_placeholder("e.g. WELCOME10").fill("TIMELESS8"); page.get_by_placeholder("e.g. WELCOME10").press("Enter"); settle(page, 2500)
    try:
        expect(page.get_by_text("TIMELESS8 applied").first).to_be_visible(timeout=8000)
    except AssertionError:
        page.screenshot(path=str(OUT / "_failure.png")); raise
    shot(page, "15_bag_with_coupon.png")
    btn(page, "Checkout").click(); page.get_by_text("Delivery address").wait_for(); settle(page, 1800)
    if page.get_by_text("Add a new address").count():
        page.get_by_label("Mobile number").fill("98765 43210"); page.get_by_label("Address line 1").fill("12 Baner Road")
        page.get_by_label("City").fill("Pune"); page.get_by_label("State").fill("Maharashtra"); page.get_by_label("PIN code").fill("411045")
        page.get_by_label("Label").fill("Home"); btn(page, "Save address").click(); settle(page, 2000)
    shot(page, "16_checkout.png")
    btn(page, "Pay ₹", exact=False).click()
    d = dialog(page); shot(page, "17_razorpay_demo_dialog.png")
    d.get_by_placeholder("success@razorpay").fill("failure@razorpay"); d.get_by_role("button", name=re.compile("Pay ₹")).first.click(); settle(page, 2000)
    expect(page.get_by_text("declined").first).to_be_visible(); shot(page, "18_payment_failed.png")
    d = dialog(page)
    d.get_by_placeholder("success@razorpay").fill("success@razorpay"); d.get_by_role("button", name=re.compile("Pay ₹")).first.click()
    page.get_by_text("your order is confirmed").wait_for(timeout=25000); settle(page, 2000); shot(page, "19_order_confirmation.png")
    btn(page, "Track order").click(); page.get_by_text("Activity").wait_for(); settle(page, 1800); shot(page, "20_order_tracking.png")

    open_piece(page, "Hermès Silk Carré 90")
    btn(page, "Add").click(); settle(page, 1500)
    btn(page, "Bag (", exact=False).click(); settle(page, 1800); btn(page, "Checkout").click(); page.get_by_text("Delivery address").wait_for(); settle(page, 1800)
    btn(page, "Pay ₹", exact=False).click()
    d = dialog(page); d.get_by_role("tab", name="Card").click(); settle(page, 700)
    d.get_by_label("Card number").fill("4111 1111 1111 1111"); d.get_by_label("Expiry (MM/YY)").fill("12/35"); d.get_by_label("CVV").fill("123")
    d.get_by_role("button", name=re.compile("Pay ₹")).first.click(); settle(page, 2000)
    expect(page.get_by_text("Test bank authentication")).to_be_visible(); shot(page, "21_bank_page.png")
    btn(page, "Success").click(); page.get_by_text("your order is confirmed").wait_for(timeout=25000); settle(page, 1500)

    open_piece(page, "Smythson Soho Notebook")
    btn(page, "Add").click(); settle(page, 1500)
    btn(page, "Bag (", exact=False).click(); settle(page, 1800); btn(page, "Checkout").click(); page.get_by_text("Delivery address").wait_for(); settle(page, 1800)
    page.get_by_text("Cash on delivery").click(); settle(page, 1500)
    btn(page, "Place order", exact=False).click(); page.get_by_text("pay on delivery").wait_for(timeout=25000); settle(page, 1500)

    btn(page, "Demo").click(); settle(page, 2200); shot(page, "22_my_orders.png")
    btn(page, "Details").click(); page.get_by_text("Activity").wait_for(); settle(page, 1500)
    btn(page, "Cancel order").click(); settle(page, 2000); shot(page, "23_order_cancelled.png")

    btn(page, "Demo").click(); settle(page, 1800); btn(page, "Sign out").click(); settle(page, 2000)
    btn(page, "Log in").click(); settle(page, 1800); btn(page, "Demo admin").click(); page.get_by_text("Admin console").first.wait_for(); settle(page, 2800)
    shot(page, "24_admin_dashboard.png")
    page.get_by_role("radio", name="Orders").click(); settle(page, 2200); shot(page, "25_admin_orders.png")
    page.get_by_role("radio", name="Products").click(); settle(page, 2400); shot(page, "26_admin_products.png")
    page.get_by_role("radio", name="Coupons").click(); settle(page, 2200); shot(page, "27_admin_coupons.png")
    page.close()

    for w, h, tag in ((390, 844, "mobile"), (820, 1100, "tablet"), (1920, 1080, "wide")):
        p = fresh(br, w, h)
        shot(p, f"28_{tag}_landing.png")
        btn(p, "Discover").click(); settle(p, 3000)
        shot(p, f"29_{tag}_collection.png"); p.close()
    br.close()
print("E2E run complete")
