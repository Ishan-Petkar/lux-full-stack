"""Shopping Cart module. One cart document per user: {_id: user_id, items: [{product_id, quantity}]}."""
from datetime import datetime, timezone

from pymongo.errors import PyMongoError

from . import config
from .errors import DatabaseError, NotFoundError, StockError, ValidationError
from .validators import clean_quantity


class CartService:
    def __init__(self, db):
        self.carts = db.carts
        self.products = db.products

    # ---------- helpers ----------
    def _items(self, user_id: str) -> list[dict]:
        doc = self.carts.find_one({"_id": user_id})
        return list(doc["items"]) if doc else []

    def _save(self, user_id: str, items: list[dict]) -> None:
        self.carts.update_one(
            {"_id": user_id},
            {"$set": {"user_id": user_id, "items": items, "updated_at": datetime.now(timezone.utc)}},
            upsert=True,
        )

    def _product(self, product_id: str) -> dict:
        p = self.products.find_one({"_id": product_id})
        if not p:
            raise NotFoundError("That product no longer exists.")
        return p

    # ---------- operations ----------
    def add(self, user_id: str, product_id: str, quantity=1) -> None:
        try:
            qty = clean_quantity(quantity)
            product = self._product(product_id)
            if product["stock"] <= 0:
                raise StockError(f"'{product['name']}' is out of stock.")
            items = self._items(user_id)
            line = next((i for i in items if i["product_id"] == product_id), None)
            new_qty = (line["quantity"] if line else 0) + qty
            if new_qty > min(product["stock"], config.MAX_LINE_QTY):
                limit = min(product["stock"], config.MAX_LINE_QTY)
                raise StockError(f"Only {limit} unit(s) of '{product['name']}' can be added to one cart.")
            if line:
                line["quantity"] = new_qty
            else:
                items.append({"product_id": product_id, "quantity": new_qty})
            self._save(user_id, items)
        except PyMongoError as exc:
            raise DatabaseError("Could not update the cart. Please try again.") from exc

    def set_quantity(self, user_id: str, product_id: str, quantity) -> None:
        try:
            qty = clean_quantity(quantity)
            product = self._product(product_id)
            limit = min(product["stock"], config.MAX_LINE_QTY)
            if qty > limit:
                raise StockError(f"Only {limit} unit(s) of '{product['name']}' available.")
            items = self._items(user_id)
            line = next((i for i in items if i["product_id"] == product_id), None)
            if not line:
                raise NotFoundError("That item is not in your cart.")
            line["quantity"] = qty
            self._save(user_id, items)
        except PyMongoError as exc:
            raise DatabaseError("Could not update the cart. Please try again.") from exc

    def remove(self, user_id: str, product_id: str) -> None:
        try:
            items = [i for i in self._items(user_id) if i["product_id"] != product_id]
            self._save(user_id, items)
        except PyMongoError as exc:
            raise DatabaseError("Could not update the cart. Please try again.") from exc

    def clear(self, user_id: str) -> None:
        try:
            self._save(user_id, [])
        except PyMongoError as exc:
            raise DatabaseError("Could not clear the cart. Please try again.") from exc

    def view(self, user_id: str) -> dict:
        """Cart enriched with current product data, line totals, grand total and any problems."""
        try:
            raw = self._items(user_id)
            lines, issues, total = [], [], 0.0
            for item in raw:
                p = self.products.find_one({"_id": item["product_id"]})
                if not p:
                    issues.append(f"A product in your cart ({item['product_id']}) is no longer sold; remove it.")
                    continue
                line_total = round(p["price"] * item["quantity"], 2)
                if item["quantity"] > p["stock"]:
                    issues.append(f"'{p['name']}': only {p['stock']} in stock, you have {item['quantity']}.")
                lines.append({"product": p, "quantity": item["quantity"],
                              "unit_price": p["price"], "line_total": line_total})
                total += line_total
            return {"lines": lines, "total": round(total, 2), "issues": issues,
                    "count": sum(l["quantity"] for l in lines)}
        except PyMongoError as exc:
            raise DatabaseError("Could not load your cart. Please try again.") from exc
