import pytest

from shop.errors import AuthError, ValidationError
from shop.users import hash_password, verify_password


def test_password_hash_roundtrip_and_salting():
    h1, h2 = hash_password("Passw0rd!"), hash_password("Passw0rd!")
    assert h1 != h2 and verify_password("Passw0rd!", h1) and not verify_password("passw0rd!", h1)
    assert "Passw0rd" not in h1 and not verify_password("x", "garbage")


def test_register_and_login(users):
    u = users.register("Asha Patil", "Asha@Example.com", "Passw0rd!")
    assert u["email"] == "asha@example.com" and u["role"] == "customer" and "password_hash" not in u
    assert users.login("ASHA@example.com", "Passw0rd!")["_id"] == u["_id"]


@pytest.mark.parametrize("pw", ["short1", "allletters", "12345678", "", "x" * 200])
def test_weak_passwords_rejected(users, pw):
    with pytest.raises(ValidationError):
        users.register("Asha Patil", "a@example.com", pw)


def test_duplicate_email_rejected(users):
    users.register("Asha Patil", "a@example.com", "Passw0rd!")
    with pytest.raises(ValidationError, match="already exists"):
        users.register("Other Name", "A@example.com", "Passw0rd!")


@pytest.mark.parametrize("email,pw", [("nobody@example.com", "Passw0rd!"), ("a@example.com", "wrong"), ("bad", "Passw0rd!"), ("", "")])
def test_login_failures_are_generic(users, email, pw):
    users.register("Asha Patil", "a@example.com", "Passw0rd!")
    with pytest.raises(AuthError, match="Incorrect email or password"):
        users.login(email, pw)


def test_change_password(users):
    u = users.register("Asha Patil", "a@example.com", "Passw0rd!")
    with pytest.raises(AuthError):
        users.change_password(u["_id"], "wrong", "NewPassw0rd")
    with pytest.raises(ValidationError):
        users.change_password(u["_id"], "Passw0rd!", "Passw0rd!")
    users.change_password(u["_id"], "Passw0rd!", "NewPassw0rd")
    assert users.login("a@example.com", "NewPassw0rd")
    with pytest.raises(AuthError):
        users.login("a@example.com", "Passw0rd!")


def test_seeded_demo_accounts(users):
    assert users.login("demo@example.com", "Demo@1234")["role"] == "customer"
    assert users.login("admin@curio.test", "Admin@1234")["role"] == "admin"


# ------------------------------------------------------------------ addresses
GOOD = dict(name="Asha Patil", phone="98765 43210", line1="12 Baner Road", city="Pune", state="Maharashtra", pincode="411045")


def test_address_book(addresses, uid):
    a = addresses.add(uid, GOOD)
    assert a["is_default"] and a["phone"] == "9876543210"
    b = addresses.add(uid, {**GOOD, "label": "Work", "pincode": "560001"})
    assert not b["is_default"]
    addresses.set_default(uid, b["_id"])
    assert addresses.list(uid)[0]["_id"] == b["_id"]
    addresses.delete(uid, b["_id"])
    assert addresses.list(uid)[0]["is_default"]                      # default falls back to the remaining address


@pytest.mark.parametrize("field,value", [("phone", "12345"), ("phone", "5876543210"), ("pincode", "012345"), ("pincode", "4110"),
                                         ("line1", "a"), ("city", ""), ("name", "1")])
def test_address_validation(addresses, uid, field, value):
    with pytest.raises(ValidationError):
        addresses.add(uid, {**GOOD, field: value})


def test_addresses_are_private(addresses, users, uid):
    a = addresses.add(uid, GOOD)
    other = users.register("Eve Hacker", "eve@example.com", "Passw0rd!")["_id"]
    with pytest.raises(Exception):
        addresses.get(other, a["_id"])


# ------------------------------------------------------------------ wishlist
def test_wishlist_toggle(wishlist, uid, P):
    a, b = P("Rolex Submariner"), P("Hermès Birkin")
    assert wishlist.toggle(uid, a) is True and wishlist.toggle(uid, b) is True
    assert wishlist.ids(uid) == [a, b]
    assert wishlist.toggle(uid, a) is False
    assert [p["_id"] for p in wishlist.products_for(uid)] == [b]
    with pytest.raises(Exception):
        wishlist.toggle(uid, "NOPE")


# ------------------------------------------------------------------ reviews
def test_reviews_and_verified_flag(reviews, cart, orders, uid, user, addr, P):
    pid = P("Smythson Soho Notebook")
    r = reviews.add(user, pid, 5, "Lovely paper", "Takes a fountain pen without any bleed through at all.")
    assert not r["verified"]
    cart.add(uid, pid, 1)
    orders.create(uid, addr, "standard", None, "cod")
    r2 = reviews.add(user, pid, 4, "Still lovely", "Updated after a month of regular daily use at my desk.")
    assert r2["verified"] and len(reviews.for_product(pid)) == 1
    s = reviews.summary(pid)
    assert s["count"] == 1 and s["avg"] == 4.0 and s["hist"][4] == 1 and reviews.summaries()[pid]["avg"] == 4.0


@pytest.mark.parametrize("rating,title,body", [(0, "ok title", "long enough review text"), (6, "ok title", "long enough review text"),
                                               (3, "x", "long enough review text"), (3, "ok title", "short")])
def test_review_validation(reviews, user, P, rating, title, body):
    with pytest.raises(ValidationError):
        reviews.add(user, P("Rolex Submariner"), rating, title, body)


# ------------------------------------------------------------------ coupons
def lines(*pairs):
    return [{"category": c, "line_total": t} for c, t in pairs]


def test_coupon_rules(coupons):
    assert coupons.evaluate("welcome10", lines(("Bags", 50000)))["discount"] == 5000
    assert coupons.evaluate("WELCOME10", lines(("Bags", 4_000_000)))["discount"] == 50000          # capped
    assert coupons.evaluate("FLAT5000", lines(("Bags", 150000)))["discount"] == 5000
    with pytest.raises(ValidationError, match="more to use"):
        coupons.evaluate("FLAT5000", lines(("Bags", 30000)))
    d = coupons.evaluate("TIMELESS8", lines(("Watches", 300000), ("Bags", 500000)))
    assert d["discount"] == 24000                                                                    # only eligible lines count
    with pytest.raises(ValidationError, match="applies only to"):
        coupons.evaluate("TIMELESS8", lines(("Bags", 500000)))
    assert coupons.evaluate("SCENT15", lines(("Fragrance", 100000)))["discount"] == 10000
    with pytest.raises(ValidationError):
        coupons.evaluate("NOPE", lines(("Bags", 50000)))


def test_coupon_inactive_expired_limit_and_create(coupons):
    from datetime import datetime, timedelta, timezone
    coupons.set_active("WELCOME10", False)
    with pytest.raises(ValidationError, match="not valid"):
        coupons.evaluate("WELCOME10", lines(("Bags", 50000)))
    c = coupons.create({"code": "OLD10", "kind": "percent", "value": 10, "expires_at": datetime.now(timezone.utc) - timedelta(days=1)})
    with pytest.raises(ValidationError, match="expired"):
        coupons.evaluate(c["_id"], lines(("Bags", 50000)))
    coupons.create({"code": "ONCE", "kind": "flat", "value": 50, "usage_limit": 1})
    coupons.redeem("ONCE")
    with pytest.raises(ValidationError, match="usage limit"):
        coupons.evaluate("ONCE", lines(("Bags", 50000)))
    with pytest.raises(ValidationError):
        coupons.create({"code": "ONCE", "kind": "flat", "value": 50})
    with pytest.raises(ValidationError):
        coupons.create({"code": "BIG", "kind": "percent", "value": 95})
