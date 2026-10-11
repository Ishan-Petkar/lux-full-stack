"""Product Management + Product Browsing & Search modules."""
import re

from pymongo.errors import PyMongoError

from .errors import DatabaseError, NotFoundError, ValidationError
from .validators import clean_product, clean_query

CATEGORY_ORDER = ["Watches", "Bags", "Jewellery", "Fragrance", "Eyewear", "Apparel", "Footwear", "Leather & Writing"]

SORTS = {
    "Featured": None,
    "Best sellers": "popular",
    "Newest": ("_id", -1),
    "Price: low to high": ("price", 1),
    "Price: high to low": ("price", -1),
    "Name: A to Z": ("name", 1),
}


def _guard(fn):
    def wrapper(*a, **kw):
        try:
            return fn(*a, **kw)
        except PyMongoError as exc:
            raise DatabaseError("The database is not responding. Please try again shortly.") from exc
    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    return wrapper


class ProductRepository:
    def __init__(self, db):
        self.col = db.products

    # ---------- read ----------
    @_guard
    def get(self, product_id: str) -> dict:
        doc = self.col.find_one({"_id": product_id})
        if not doc:
            raise NotFoundError("That product no longer exists.")
        return doc

    @_guard
    def all(self) -> list[dict]:
        return list(self.col.find().sort("_id", 1))

    @_guard
    def categories(self) -> list[str]:
        found = set(self.col.distinct("category"))
        return [c for c in CATEGORY_ORDER if c in found] + sorted(found - set(CATEGORY_ORDER))

    @_guard
    def subcategories(self, category: str) -> list[str]:
        return sorted(self.col.distinct("subcategory", {"category": category}))

    @_guard
    def brands(self, category: str | None = None) -> list[str]:
        flt = {"category": category} if category and category != "All" else {}
        return sorted(self.col.distinct("brand", flt))

    @_guard
    def price_bounds(self) -> tuple[int, int]:
        prices = [p["price"] for p in self.col.find({}, {"price": 1})]
        return (int(min(prices)), int(max(prices)) + 1) if prices else (0, 1)

    @_guard
    def search(self, query: str = "", category: str | None = None,
               in_stock_only: bool = False, sort: str = "Featured", brands: list[str] | None = None,
               price_range: tuple[float, float] | None = None, popularity: dict[str, int] | None = None, subcategory: str | None = None) -> list[dict]:
        """Keyword search (every word must match name/brand/category/tags/description) with brand / price filters."""
        query = clean_query(query)
        clauses = []
        for term in query.split():
            rx = {"$regex": re.escape(term), "$options": "i"}
            clauses.append({"$or": [{"name": rx}, {"brand": rx}, {"category": rx},
                                    {"subcategory": rx}, {"tags": rx}, {"description": rx}]})
        flt: dict = {"$and": clauses} if clauses else {}
        if category and category != "All":
            flt["category"] = category
        if subcategory and subcategory != "All":
            flt["subcategory"] = subcategory
        if in_stock_only:
            flt["stock"] = {"$gt": 0}
        if brands:
            flt["brand"] = {"$in": list(brands)}
        if price_range:
            flt["price"] = {"$gte": price_range[0], "$lte": price_range[1]}
        spec = SORTS.get(sort)
        if spec == "popular":
            rows = list(self.col.find(flt).sort("_id", 1))
            pop = popularity or {}
            return sorted(rows, key=lambda p: -pop.get(p["_id"], 0))
        cursor = self.col.find(flt)
        cursor = cursor.sort(*spec) if spec else cursor.sort("_id", 1)
        return list(cursor)

    # ---------- write (product management) ----------
    @_guard
    def add(self, data: dict) -> dict:
        doc = clean_product(data)
        pid = str(data.get("product_id") or "").strip().upper()
        if not pid:
            n = self.col.count_documents({}) + 1
            pid = f"P{n:03d}"
            while self.col.find_one({"_id": pid}):
                n += 1
                pid = f"P{n:03d}"
        elif self.col.find_one({"_id": pid}):
            raise ValidationError(f"Product id {pid} already exists.")
        doc["_id"] = pid
        self.col.insert_one(doc)
        return doc

    @_guard
    def update(self, product_id: str, data: dict) -> dict:
        self.get(product_id)
        doc = clean_product(data)
        self.col.update_one({"_id": product_id}, {"$set": doc})
        return self.get(product_id)

    @_guard
    def delete(self, product_id: str) -> None:
        if not self.col.delete_one({"_id": product_id}).deleted_count:
            raise NotFoundError("That product no longer exists.")
