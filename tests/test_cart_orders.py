from datetime import datetime, timedelta, timezone

import pytest

from shop.errors import AuthError, NotFoundError, PaymentError, StockError, ValidationError

NOTEBOOK, LIGHTER, WATCH, SWEATER = "Smythson Soho Notebook", "Dunhill Rollagas Lighter", "Rolex Submariner", "Loro Piana Cashmere Crewneck"
SILK = "Hermès Silk Carré 90"          # under the 50,000 cash-on-delivery limit


# ------------------------------------------------------------------ bag
def test_add_and_total(cart, uid, P, price):
    a, b = P(NOTEBOOK), P(LIGHTER)
    cart.add(uid, a, 2)
    cart.add(uid, b, 1)
    cart.add(uid, a, 1)                                   # merges -> qty 3
    v = cart.view(uid)
    assert v["count"] == 4 and v["total"] == 3 * price(a) + price(b) and len(v["lines"]) == 2


def test_update_and_remove(cart, uid, P, price):
    a = P(NOTEBOOK)
    cart.add(uid, a, 1)
    cart.set_quantity(uid, a, 5)
    assert cart.view(uid)["total"] == 5 * price(a)
    cart.remove(uid, a)
    assert cart.view(uid)["lines"] == []


@pytest.mark.parametrize("qty", [0, -2, "x", 1.5, 11])
def test_invalid_quantity_rejected(cart, uid, P, qty):
    with pytest.raises(ValidationError):
        cart.add(uid, P(NOTEBOOK), qty)


def test_sold_out_cannot_be_added(cart, uid, P):
    with pytest.raises(StockError):
        cart.add(uid, P("Patek Philippe Nautilus"), 1)          # stock 0


def test_cannot_exceed_stock(cart, uid, P):
    w = P(WATCH)                                               # stock 5
    cart.add(uid, w, 3)
    with pytest.raises(StockError):
        cart.add(uid, w, 3)


def test_unknown_product_and_missing_line(cart, uid, P):
    with pytest.raises(NotFoundError):
        cart.add(uid, "NOPE", 1)
    with pytest.raises(NotFoundError):
        cart.set_quantity(uid, P(NOTEBOOK), 2)


def test_carts_are_per_user(cart, users, uid, P):
    other = users.register("Bob Rao", "b@example.com", "Passw0rd!")["_id"]
    cart.add(uid, P(NOTEBOOK), 1)
    assert cart.view(other)["lines"] == []


# ------------------------------------------------------------------ checkout: cash on delivery
def test_cod_order_end_to_end(cart, orders, repo, uid, addr, P, price):
    n, s = P(NOTEBOOK), P(LIGHTER)
    cart.add(uid, n, 1)
    cart.add(uid, s, 1)
    before = (repo.get(n)["stock"], repo.get(s)["stock"])
    o = orders.create(uid, addr, "standard", None, "cod")
    assert o["status"] == "Placed" and o["payment"] == {"method": "cod", "status": "pending"}
    assert o["pricing"]["subtotal"] == price(n) + price(s) and o["pricing"]["shipping"] == 0       # complimentary above 10,000
    assert o["total"] == o["pricing"]["total"] and o["pricing"]["gst_included"] > 0
    assert repo.get(n)["stock"] == before[0] - 1 and repo.get(s)["stock"] == before[1] - 1
    assert cart.view(uid)["lines"] == [] and orders.history(uid)[0]["_id"] == o["_id"]


def test_shipping_fee_below_threshold_and_express(cart, orders, uid, addr, P, price):
    n = P(NOTEBOOK)
    cart.add(uid, n, 1)
    o = orders.create(uid, addr, "standard", None, "cod")
    assert o["pricing"]["shipping"] == 250 and o["total"] == price(n) + 250
    cart.add(uid, n, 1)
    assert orders.create(uid, addr, "express", None, "cod")["pricing"]["shipping"] == 1200


def test_order_snapshot_keeps_price(cart, orders, repo, uid, addr, P):
    n = P(NOTEBOOK)
    cart.add(uid, n, 1)
    o = orders.create(uid, addr, "standard", None, "cod")
    base = {k: repo.get(n)[k] for k in ("name", "description", "category", "brand", "stock", "tags")}
    old = repo.get(n)["price"]
    repo.update(n, {**base, "price": 999999})
    assert orders.history(uid)[0]["items"][0]["unit_price"] == old == o["items"][0]["unit_price"]


def test_empty_bag_and_bad_address(cart, orders, uid, addr, P):
    with pytest.raises(ValidationError):
        orders.create(uid, addr, "standard", None, "cod")
    cart.add(uid, P(NOTEBOOK), 1)
    with pytest.raises(ValidationError):
        orders.create(uid, "A-nope", "standard", None, "cod")
    with pytest.raises(ValidationError):
        orders.create(uid, addr, "standard", None, "bitcoin")


def test_cod_limit(cart, orders, uid, addr, P):
    cart.add(uid, P(WATCH), 1)                                  # far above 50,000
    with pytest.raises(ValidationError, match="Cash on delivery"):
        orders.create(uid, addr, "standard", None, "cod")


def test_stock_rechecked_and_rolled_back(cart, orders, repo, db, uid, addr, P):
    n, s = P(NOTEBOOK), P(SILK)
    cart.add(uid, n, 2)
    cart.add(uid, s, 3)
    db.products.update_one({"_id": s}, {"$set": {"stock": 1}})
    stock = repo.get(n)["stock"]
    with pytest.raises(StockError):
        orders.create(uid, addr, "standard", None, "cod")
    assert repo.get(n)["stock"] == stock and orders.history(uid) == [] and cart.view(uid)["count"] == 5


def test_reservation_failure_rolls_back(cart, orders, repo, uid, addr, P):
    n, s = P(NOTEBOOK), P(LIGHTER)
    cart.add(uid, n, 1)
    cart.add(uid, s, 1)
    col = orders.products
    real = col.update_one
    calls = {"n": 0}

    def flaky(flt, upd, *a, **k):
        if "$inc" in upd and upd["$inc"]["stock"] < 0:
            calls["n"] += 1
            if calls["n"] == 2:                                  # someone else buys the last piece right now
                real({"_id": s}, {"$set": {"stock": 0}})
        return real(flt, upd, *a, **k)

    stock = repo.get(n)["stock"]
    import pytest as _p
    mp = _p.MonkeyPatch()
    mp.setattr(col, "update_one", flaky)
    try:
        with pytest.raises(StockError):
            orders.create(uid, addr, "standard", None, "cod")
    finally:
        mp.undo()
    assert repo.get(n)["stock"] == stock and orders.history(uid) == []


# ------------------------------------------------------------------ coupons at checkout
def test_coupon_applied_and_redeemed_only_after_payment(cart, orders, coupons, uid, addr, P):
    cart.add(uid, P(WATCH), 1)
    with pytest.raises(ValidationError):
        orders.create(uid, addr, "standard", "NOPE123", "razorpay")
    o = orders.create(uid, addr, "standard", "WELCOME10", "razorpay")
    assert o["pricing"]["coupon_code"] == "WELCOME10" and o["pricing"]["discount"] == 50000.0           # capped
    assert coupons.get("WELCOME10")["used"] == 0


# ------------------------------------------------------------------ online payment (demo Razorpay)
def pay_ok(orders, payments, uid, order):
    rz = orders.start_payment(order["_id"], uid)
    res = payments.authorize(rz["id"], "upi", {"vpa": "success@razorpay"})
    assert res["next"] == "paid"
    return orders.confirm_payment(order["_id"], uid, res["payment"])


def test_online_payment_happy_path(cart, orders, payments, coupons, uid, addr, P):
    cart.add(uid, P(SWEATER), 1)
    cart.add(uid, P(NOTEBOOK), 1)
    o = orders.create(uid, addr, "standard", "WELCOME10", "razorpay")
    assert o["status"] == "Pending Payment" and cart.view(uid)["lines"] == []
    paid = pay_ok(orders, payments, uid, o)
    assert paid["status"] == "Placed" and paid["payment"]["status"] == "paid" and paid["payment"]["payment_id"].startswith("pay_")
    assert [t["status"] for t in paid["timeline"]] == ["Pending Payment", "Placed"]
    assert coupons.get("WELCOME10")["used"] == 1
    assert payments.col.find_one({"_id": paid["payment"]["gateway_order_id"]})["status"] == "captured"


def test_card_flow_with_bank_page(cart, orders, payments, uid, addr, P):
    cart.add(uid, P(SWEATER), 1)
    o = orders.create(uid, addr, "standard", None, "razorpay")
    rz = orders.start_payment(o["_id"], uid)
    r = payments.authorize(rz["id"], "card", {"number": "4111 1111 1111 1111", "expiry": "12/35", "cvv": "123", "holder": "Test User"})
    assert r["next"] == "bank"
    assert orders.confirm_payment(o["_id"], uid, payments.bank_result(rz["id"], True))["status"] == "Placed"
    rec = payments.col.find_one({"_id": rz["id"]})
    assert rec["last4"] == "1111" and "4111111111111111" not in str(rec)


@pytest.mark.parametrize("method,details", [
    ("card", {"number": "4242 4242 4242 4242", "expiry": "12/35", "cvv": "123", "holder": "Test User"}),
    ("card", {"number": "1234 5678 9012 3456", "expiry": "12/35", "cvv": "123", "holder": "Test User"}),
    ("card", {"number": "4111 1111 1111 1111", "expiry": "01/20", "cvv": "123", "holder": "Test User"}),
    ("upi", {"vpa": "failure@razorpay"}), ("upi", {"vpa": "random@bank"}), ("upi", {"vpa": "not a vpa"}),
])
def test_failed_payments_keep_order_pending(cart, orders, payments, uid, addr, P, method, details):
    cart.add(uid, P(SWEATER), 1)
    o = orders.create(uid, addr, "standard", None, "razorpay")
    rz = orders.start_payment(o["_id"], uid)
    with pytest.raises((PaymentError, ValidationError)) as e:
        payments.authorize(rz["id"], method, details)
    orders.payment_failed(o["_id"], str(e.value))
    cur = orders.get(o["_id"], uid)
    assert cur["status"] == "Pending Payment" and cur["payment"]["status"] == "failed"


def test_bank_page_failure_then_retry_succeeds(cart, orders, payments, uid, addr, P):
    cart.add(uid, P(SWEATER), 1)
    o = orders.create(uid, addr, "standard", None, "razorpay")
    rz = orders.start_payment(o["_id"], uid)
    payments.authorize(rz["id"], "netbanking", {"bank": "HDFC Bank"})
    with pytest.raises(PaymentError):
        payments.bank_result(rz["id"], False)
    rz2 = orders.start_payment(o["_id"], uid)
    assert rz2["id"] != rz["id"]
    res = payments.authorize(rz2["id"], "upi", {"vpa": "success@razorpay"})
    assert orders.confirm_payment(o["_id"], uid, res["payment"])["status"] == "Placed"


def test_tampered_signature_and_wrong_order_rejected(cart, orders, payments, uid, addr, P):
    cart.add(uid, P(SWEATER), 1)
    o = orders.create(uid, addr, "standard", None, "razorpay")
    rz = orders.start_payment(o["_id"], uid)
    res = payments.authorize(rz["id"], "upi", {"vpa": "success@razorpay"})["payment"]
    with pytest.raises(PaymentError, match="verification failed"):
        orders.confirm_payment(o["_id"], uid, {**res, "razorpay_signature": "0" * 64})
    assert orders.get(o["_id"], uid)["status"] == "Pending Payment"
    with pytest.raises(PaymentError, match="does not belong"):
        orders.confirm_payment(o["_id"], uid, {**res, "razorpay_order_id": "order_other"})


def test_amount_mismatch_rejected(cart, orders, payments, db, uid, addr, P):
    cart.add(uid, P(SWEATER), 1)
    o = orders.create(uid, addr, "standard", None, "razorpay")
    rz = orders.start_payment(o["_id"], uid)
    res = payments.authorize(rz["id"], "upi", {"vpa": "success@razorpay"})["payment"]
    db.payments.update_one({"_id": rz["id"]}, {"$set": {"amount": 100}})
    with pytest.raises(PaymentError, match="amount"):
        orders.confirm_payment(o["_id"], uid, res)


def test_other_users_cannot_pay_or_cancel(cart, orders, users, uid, addr, P):
    cart.add(uid, P(SWEATER), 1)
    o = orders.create(uid, addr, "standard", None, "razorpay")
    other = users.register("Eve Hacker", "eve@example.com", "Passw0rd!")["_id"]
    with pytest.raises(NotFoundError):
        orders.start_payment(o["_id"], other)
    with pytest.raises(NotFoundError):
        orders.cancel(o["_id"], other)


# ------------------------------------------------------------------ cancel / refund / expiry / admin
def test_cancel_paid_order_restocks_and_refunds(cart, orders, payments, repo, uid, addr, P):
    s = P(SWEATER)
    stock = repo.get(s)["stock"]
    cart.add(uid, s, 2)
    o = pay_ok(orders, payments, uid, orders.create(uid, addr, "standard", None, "razorpay"))
    assert repo.get(s)["stock"] == stock - 2
    c = orders.cancel(o["_id"], uid)
    assert c["status"] == "Cancelled" and c["payment"]["status"] == "refunded" and repo.get(s)["stock"] == stock
    assert payments.col.find_one({"_id": o["payment"]["gateway_order_id"]})["status"] == "refunded"
    with pytest.raises(ValidationError):
        orders.cancel(o["_id"], uid)


def test_cannot_cancel_after_shipping(cart, orders, users, uid, addr, P):
    cart.add(uid, P(NOTEBOOK), 1)
    o = orders.create(uid, addr, "standard", None, "cod")
    admin = users.register("Admin One", "a1@example.com", "Passw0rd!", role="admin")
    orders.set_status(o["_id"], "Packed", admin)
    orders.set_status(o["_id"], "Shipped", admin)
    with pytest.raises(ValidationError, match="no longer be cancelled"):
        orders.cancel(o["_id"], uid)


def test_pending_orders_expire_and_release_stock(cart, orders, repo, db, uid, addr, P):
    s = P(SWEATER)
    stock = repo.get(s)["stock"]
    cart.add(uid, s, 2)
    o = orders.create(uid, addr, "standard", None, "razorpay")
    assert repo.get(s)["stock"] == stock - 2
    db.orders.update_one({"_id": o["_id"]}, {"$set": {"created_at": datetime.now(timezone.utc) - timedelta(minutes=30)}})
    assert orders.expire_pending() == 1
    assert repo.get(s)["stock"] == stock and orders.get(o["_id"])["status"] == "Cancelled"
    with pytest.raises(PaymentError, match="expired|awaiting"):
        orders.start_payment(o["_id"], uid)


def test_status_flow_and_admin_only(cart, orders, users, uid, addr, P):
    cart.add(uid, P(NOTEBOOK), 1)
    o = orders.create(uid, addr, "standard", None, "cod")
    with pytest.raises(AuthError):
        orders.set_status(o["_id"], "Packed", users.get(uid))
    admin = users.register("Admin Two", "a2@example.com", "Passw0rd!", role="admin")
    with pytest.raises(ValidationError):
        orders.set_status(o["_id"], "Delivered", admin)
    for st in ("Packed", "Shipped", "Delivered"):
        done = orders.set_status(o["_id"], st, admin)
    assert done["status"] == "Delivered" and done["payment"]["status"] == "paid"
    assert [t["status"] for t in done["timeline"]] == ["Placed", "Packed", "Shipped", "Delivered"]
