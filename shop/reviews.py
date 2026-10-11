"""Customer reviews: one per user per product, with a verified-buyer flag."""
from datetime import datetime, timezone

from pymongo.errors import PyMongoError

from .errors import DatabaseError, NotFoundError
from .validators import clean_review


class ReviewService:
    def __init__(self, db):
        self.col, self.products, self.orders = db.reviews, db.products, db.orders

    def has_bought(self, user_id: str, product_id: str) -> bool:
        return self.orders.count_documents({"user_id": user_id, "items.product_id": product_id,
                                            "status": {"$in": ["Placed", "Packed", "Shipped", "Delivered"]}}) > 0

    def add(self, user: dict, product_id: str, rating, title, body) -> dict:
        rating, title, body = clean_review(rating, title, body)
        try:
            if not self.products.find_one({"_id": product_id}, {"_id": 1}):
                raise NotFoundError("That product no longer exists.")
            doc = {"product_id": product_id, "user_id": user["_id"], "user_name": user["name"], "rating": rating, "title": title,
                   "body": body, "verified": self.has_bought(user["_id"], product_id), "created_at": datetime.now(timezone.utc)}
            self.col.update_one({"product_id": product_id, "user_id": user["_id"]},
                                {"$set": doc, "$setOnInsert": {"_id": f"R-{product_id}-{user['_id']}"}}, upsert=True)
            return doc
        except PyMongoError as exc:
            raise DatabaseError("Could not save your review.") from exc

    def for_product(self, product_id: str, limit: int = 20) -> list[dict]:
        return list(self.col.find({"product_id": product_id}).sort("created_at", -1).limit(limit))

    def summary(self, product_id: str) -> dict:
        rows = list(self.col.find({"product_id": product_id}, {"rating": 1}))
        hist = {i: sum(1 for r in rows if r["rating"] == i) for i in range(1, 6)}
        n = len(rows)
        return {"count": n, "avg": round(sum(r["rating"] for r in rows) / n, 1) if n else 0.0, "hist": hist}

    def summaries(self) -> dict[str, dict]:
        """{product_id: {avg, count}} for every reviewed product (used on product cards)."""
        acc: dict[str, list[int]] = {}
        for r in self.col.find({}, {"product_id": 1, "rating": 1}):
            acc.setdefault(r["product_id"], []).append(r["rating"])
        return {k: {"count": len(v), "avg": round(sum(v) / len(v), 1)} for k, v in acc.items()}
