"""Wishlist: one document per user holding product ids."""
from pymongo.errors import PyMongoError

from .errors import DatabaseError, NotFoundError


class WishlistService:
    def __init__(self, db):
        self.col, self.products = db.wishlists, db.products

    def ids(self, user_id: str) -> list[str]:
        try:
            doc = self.col.find_one({"_id": user_id})
        except PyMongoError as exc:
            raise DatabaseError("Could not load your wishlist.") from exc
        return list(doc["product_ids"]) if doc else []

    def toggle(self, user_id: str, product_id: str) -> bool:
        """Add or remove; returns True when the product is now saved."""
        try:
            if not self.products.find_one({"_id": product_id}, {"_id": 1}):
                raise NotFoundError("That product no longer exists.")
            ids = self.ids(user_id)
            saved = product_id not in ids
            ids = [*ids, product_id] if saved else [i for i in ids if i != product_id]
            self.col.update_one({"_id": user_id}, {"$set": {"product_ids": ids}}, upsert=True)
            return saved
        except PyMongoError as exc:
            raise DatabaseError("Could not update your wishlist.") from exc

    def products_for(self, user_id: str) -> list[dict]:
        ids = self.ids(user_id)
        found = {p["_id"]: p for p in self.products.find({"_id": {"$in": ids}})}
        return [found[i] for i in ids if i in found]
