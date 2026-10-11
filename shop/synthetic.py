"""Synthetic purchase history used to bootstrap 'frequently bought together'.

A new store has no orders yet, so the analysis would have nothing to learn from. We therefore generate ~900 past
orders from realistic shopping 'missions' (e.g. watch collector: sports watch + chronograph + wallet + pen). These orders are flagged
`synthetic: true`, belong to the placeholder user U-seed, never change stock, and are excluded from the admin revenue
figures unless asked. Real orders placed in the app are added to the same pool and shift the statistics over time.
"""
import random
import uuid
from datetime import datetime, timedelta, timezone

from . import config

# (weight, name, [(subcategory, probability of including an item from it, max items)])
MISSIONS = [
    (12, "Watch collector", [("Sports watches", 1.0, 1), ("Chronographs", 0.6, 1), ("Dress watches", 0.5, 1), ("Belts & wallets", 0.5, 1), ("Writing", 0.3, 1)]),
    (10, "Executive upgrade", [("Dress watches", 0.8, 1), ("Belts & wallets", 1.0, 2), ("Writing", 0.7, 1), ("Loafers & oxfords", 0.6, 1), ("Men's fragrance", 0.5, 1)]),
    (10, "The gift", [("Women's fragrance", 1.0, 1), ("Necklaces & earrings", 0.7, 1), ("Knitwear & silk", 0.6, 1), ("Bracelets & rings", 0.4, 1)]),
    (9, "Evening", [("Heels", 1.0, 1), ("Handbags", 1.0, 1), ("Necklaces & earrings", 0.7, 1), ("Women's fragrance", 0.5, 1), ("Sunglasses", 0.3, 1)]),
    (9, "Wardrobe edit", [("Outerwear", 1.0, 1), ("Knitwear & silk", 0.9, 1), ("Loafers & oxfords", 0.6, 1), ("Sunglasses", 0.4, 1)]),
    (8, "Tailoring", [("Tailoring", 1.0, 1), ("Loafers & oxfords", 0.9, 1), ("Belts & wallets", 0.8, 1), ("Dress watches", 0.5, 1), ("Men's fragrance", 0.4, 1)]),
    (8, "Travel", [("Travel bags", 1.0, 2), ("Sunglasses", 0.7, 1), ("Belts & wallets", 0.5, 1), ("Unisex fragrance", 0.4, 1)]),
    (7, "Jewellery moment", [("Bracelets & rings", 1.0, 2), ("Necklaces & earrings", 0.8, 1), ("Handbags", 0.3, 1)]),
    (7, "Signature scent", [("Men's fragrance", 0.8, 1), ("Women's fragrance", 0.6, 1), ("Unisex fragrance", 0.8, 1)]),
    (6, "Weekend", [("Sneakers", 1.0, 1), ("Sunglasses", 0.8, 1), ("Knitwear & silk", 0.6, 1), ("Travel bags", 0.4, 1)]),
    (6, "Desk and study", [("Writing", 1.0, 2), ("Belts & wallets", 0.6, 1)]),
]


def generate(products: list[dict], n: int = 900, seed: int = 7) -> list[dict]:
    rng = random.Random(seed)
    by_sub: dict[str, list[dict]] = {}
    for p in products:
        by_sub.setdefault(p["subcategory"], []).append(p)
    now = datetime.now(timezone.utc)
    weights = [m[0] for m in MISSIONS]
    orders = []
    for _ in range(n):
        _, _, parts = rng.choices(MISSIONS, weights)[0]
        picked: list[dict] = []
        for sub, prob, mx in parts:
            if rng.random() <= prob and sub in by_sub:
                for p in rng.sample(by_sub[sub], k=min(rng.randint(1, mx), len(by_sub[sub]))):
                    if p not in picked:
                        picked.append(p)
        if rng.random() < 0.10:                                   # occasional impulse item
            p = rng.choice(products)
            if p not in picked:
                picked.append(p)
        if len(picked) < 2:
            continue
        created = now - timedelta(days=rng.randint(2, 240), hours=rng.randint(0, 23), minutes=rng.randint(0, 59))
        items = [{"product_id": p["_id"], "name": p["name"], "brand": p["brand"], "category": p["category"], "unit_price": p["price"],
                  "quantity": 1, "line_total": p["price"], "image": ""} for p in picked]
        subtotal = round(sum(i["line_total"] for i in items), 2)
        fee = 0.0 if subtotal >= config.FREE_SHIPPING_MIN else float(config.SHIPPING["standard"]["fee"])
        total = round(subtotal + fee, 2)
        method = "cod" if total <= 50000 and rng.random() < 0.3 else "razorpay"
        status = rng.choices(["Delivered", "Shipped", "Packed", "Placed", "Cancelled"], [86, 5, 3, 2, 4])[0] if (now - created).days < 20 else rng.choices(["Delivered", "Cancelled"], [96, 4])[0]
        orders.append({
            "_id": f"ORD-{created:%Y%m%d}-S{uuid.UUID(int=rng.getrandbits(128)).hex[:5].upper()}", "user_id": "U-seed", "items": items,
            "pricing": {"subtotal": subtotal, "discount": 0.0, "coupon_code": None, "shipping": fee, "shipping_method": "standard",
                        "gst_included": round(subtotal * config.GST_RATE / (1 + config.GST_RATE), 2), "total": round(subtotal + fee, 2)},
            "total": round(subtotal + fee, 2), "address": {"label": "Seed", "name": "Seed Customer", "phone": "9000000000", "line1": "Seeded history",
                                                           "line2": "", "city": "Pune", "state": "Maharashtra", "pincode": "411045"},
            "payment": {"method": method, "status": "refunded" if status == "Cancelled" else ("paid" if method == "razorpay" or status == "Delivered" else "pending")}, "status": status,
            "timeline": [{"status": status, "at": created, "note": "Seeded history"}],
            "created_at": created, "updated_at": created, "synthetic": True})
    return orders
