from shop import config, pricing
from shop.brands import facts
from shop.invoice import invoice_html
from shop.stats import dashboard


def cats(db, rows):
    return {db.products.find_one({"_id": r["product_id"]})["category"] for r in rows}


def subs(db, rows):
    return {db.products.find_one({"_id": r["product_id"]})["subcategory"] for r in rows}


def test_sports_watch_is_bought_with_leather_and_writing(bundles, db, P):
    rows = bundles.together(P("Rolex Submariner"))
    assert rows and all(r["orders"] >= 2 and r["lift"] > 1 for r in rows)
    assert subs(db, rows) & {"Belts & wallets", "Chronographs", "Dress watches", "Writing"}


def test_heels_are_bought_with_bags_and_jewellery(bundles, db, P):
    rows = bundles.together(P("Christian Louboutin So Kate Pump"))
    assert rows and cats(db, rows) & {"Bags", "Jewellery", "Fragrance", "Eyewear"}


def test_bundle_stats_are_consistent(bundles, P):
    for r in bundles.together(P("Rolex Submariner"), k=10):
        assert 0 < r["confidence"] <= 1
    assert len(bundles.together(P("Rolex Submariner"), k=2)) <= 2
    assert bundles.together("NOPE") == []


def test_bundles_learn_from_new_orders(bundles, cart, orders, uid, addr, P):
    n = P("Smythson Soho Notebook")
    before = bundles.order_count(n)
    cart.add(uid, n, 1)
    orders.create(uid, addr, "standard", None, "cod")
    assert bundles.order_count(n) == before + 1


def test_popularity(bundles):
    pop = bundles.popularity()
    assert pop and max(pop.values()) > 5


def test_synthetic_history_flagged_and_stock_untouched(db, P):
    assert db.orders.count_documents({"synthetic": True}) > 500
    assert db.orders.count_documents({"synthetic": {"$ne": True}}) == 0
    assert db.products.find_one({"_id": P("Rolex Submariner")})["stock"] == 5


def test_pricing_quote():
    q = pricing.quote(5000, 0, "standard")
    assert q["shipping"] == 250 and q["total"] == 5250
    q = pricing.quote(250000, 5000, "standard")
    assert q["shipping"] == 0 and q["total"] == 245000 and q["gst_included"] == round(245000 * 0.18 / 1.18, 2)
    assert pricing.quote(250000, 0, "express")["shipping"] == 1200
    lo, hi = pricing.eta_days("411045", "standard")
    assert pricing.eta_days("781001", "standard") == (lo + 2, hi + 2) and pricing.eta_days("411045", "express")[0] < lo


def test_brand_facts():
    assert facts("Rolex") == "Switzerland · est. 1905" and facts("Unknown") == ""


def test_invoice_contains_key_facts(cart, orders, uid, addr, P):
    cart.add(uid, P("Smythson Soho Notebook"), 1)
    o = orders.create(uid, addr, "standard", None, "cod")
    html = invoice_html(o)
    assert o["_id"] in html and "Soho Notebook" in html and "Includes GST" in html and "12 Baner Road" in html and "<script" not in html


def test_dashboard_excludes_synthetic_by_default(db, cart, orders, uid, addr, P):
    assert dashboard(db)["orders"] == 0
    cart.add(uid, P("Rolex Submariner"), 1)
    orders.create(uid, addr, "standard", None, "razorpay")                       # pending: not revenue yet
    d = dashboard(db)
    assert d["orders"] == 1 and d["revenue"] == 0
    full = dashboard(db, include_synthetic=True)
    assert full["revenue"] > 100_000_000 and full["top_products"] and full["category_revenue"]
    assert any(p["stock"] == 0 for p in full["low_stock"])
