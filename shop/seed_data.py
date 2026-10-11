"""Demo data: the luxury catalogue (shop/catalog_data.json, built by scripts/finalize_catalog.py from real Wikipedia / Unsplash data),
two demo accounts, coupons and a synthetic purchase history.

`subcategory` is a human-assigned label. It is NOT a recommendation feature; scripts/evaluate.py uses it as a relevance proxy.
"""
import json
from datetime import datetime, timezone

from . import config
from .db import ensure_indexes

CATALOG_FILE = config.ROOT / "shop" / "catalog_data.json"
SCHEMA_VERSION = 5          # bump when the demo data model changes: demo collections are rebuilt on next start
DEMO_USERS = [("Demo Customer", "demo@example.com", "Demo@1234", "customer"),
              ("Store Admin", "admin@curio.test", "Admin@1234", "admin")]
COUPONS = [
    {"_id": "WELCOME10", "kind": "percent", "value": 10, "min_order": 20000, "max_discount": 50000, "categories": None,
     "label": "10% off your first order (up to 50,000)", "active": True, "used": 0, "usage_limit": None, "expires_at": None},
    {"_id": "FLAT5000", "kind": "flat", "value": 5000, "min_order": 100000, "max_discount": None, "categories": None,
     "label": "5,000 off orders above 1,00,000", "active": True, "used": 0, "usage_limit": None, "expires_at": None},
    {"_id": "TIMELESS8", "kind": "percent", "value": 8, "min_order": 200000, "max_discount": 150000, "categories": ["Watches", "Jewellery"],
     "label": "8% off watches and jewellery above 2,00,000", "active": True, "used": 0, "usage_limit": None, "expires_at": None},
    {"_id": "SCENT15", "kind": "percent", "value": 15, "min_order": 15000, "max_discount": 10000, "categories": ["Fragrance"],
     "label": "15% off fragrance above 15,000", "active": True, "used": 0, "usage_limit": None, "expires_at": None},
]


def build_documents() -> list[dict]:
    rows = json.loads(CATALOG_FILE.read_text())
    return [{"_id": r["id"], "name": r["name"], "brand": r["brand"], "category": r["category"], "subcategory": r["subcategory"],
             "price": float(r["price"]), "stock": r["stock"], "image": "", "tags": r["tags"], "description": r["description"],
             "source": r.get("source", "")} for r in rows]


def featured_ids() -> list[str]:
    """Landing-page picks: the first in-stock product of a few signature maisons."""
    want = ["Rolex Submariner", "Hermès Birkin", "Chanel Classic Flap (2.55)", "Cartier Love Bracelet", "Omega Speedmaster Professional",
            "Burberry Kensington Trench Coat", "Chanel N°5 Eau de Parfum", "Patek Philippe Nautilus"]
    rows = json.loads(CATALOG_FILE.read_text())
    key = {f"{r['brand']} {r['name']}": r["id"] for r in rows}
    return [key[w] for w in want if w in key]


def attach_images(db) -> int:
    """Point products at assets/products/<id>.jpg when that photo exists (idempotent; keeps URLs / uploads)."""
    n = 0
    for p in db.products.find({}, {"image": 1}):
        rel = f"assets/products/{p['_id']}.jpg"
        cur = p.get("image") or ""
        if cur != rel and not cur.startswith(("http://", "https://", "assets/")) and (config.ROOT / rel).is_file():
            db.products.update_one({"_id": p["_id"]}, {"$set": {"image": rel}})
            n += 1
    return n


def seed_if_empty(db, force: bool = False) -> bool:
    """Create indexes and load demo data (catalogue, users, coupons, synthetic purchase history). Returns True if seeded."""
    from .synthetic import generate
    from .users import hash_password

    ensure_indexes(db)
    meta = db.meta.find_one({"_id": "schema"})
    if force or not meta or meta.get("version", 0) < SCHEMA_VERSION:
        for c in ("products", "users", "carts", "orders", "wishlists", "reviews", "coupons", "addresses", "payments"):
            db[c].delete_many({})
    if db.products.count_documents({}) > 0:
        attach_images(db)
        return False
    docs = build_documents()
    db.products.insert_many(docs)
    now = datetime.now(timezone.utc)
    for name, email, pw, role in DEMO_USERS:
        db.users.insert_one({"_id": "U-demo0001" if role == "customer" else "U-admin001", "name": name, "email": email, "role": role,
                             "password_hash": hash_password(pw), "created_at": now})
    db.coupons.insert_many(COUPONS)
    db.orders.insert_many(generate(docs))
    db.meta.update_one({"_id": "schema"}, {"$set": {"version": SCHEMA_VERSION, "seeded_at": now}}, upsert=True)
    attach_images(db)
    return True
