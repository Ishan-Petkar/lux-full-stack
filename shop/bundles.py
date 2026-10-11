"""'Frequently bought together' - market-basket analysis over completed orders.

For a product p and another product q (over baskets that were actually placed):
    confidence(p -> q) = orders(p and q) / orders(p)         "X% of people who bought p also bought q"
    lift(p -> q)       = confidence / (orders(q) / all orders)   > 1 means q is bought with p more often than by chance
Ranking is by confidence x lift, with a minimum support of 2 orders so one-off baskets never surface.
The analysis is rebuilt only when the order data changes.
"""
from .orders import ACTIVE


class BundleService:
    def __init__(self, db):
        self.orders = db.orders
        self._fp = None
        self._baskets: list[frozenset] = []
        self._count: dict[str, int] = {}
        self._pair: dict[tuple[str, str], int] = {}
        self._units: dict[str, int] = {}

    def _fingerprint(self):
        last = next(iter(self.orders.find({}, {"updated_at": 1}).sort("updated_at", -1).limit(1)), None)
        return (self.orders.count_documents({}), last["updated_at"] if last else None)

    def _build(self):
        fp = self._fingerprint()
        if fp == self._fp:
            return
        baskets, count, pair, units = [], {}, {}, {}
        for o in self.orders.find({"status": {"$in": ACTIVE}}, {"items.product_id": 1, "items.quantity": 1}):
            ids = sorted({i["product_id"] for i in o["items"]})
            baskets.append(frozenset(ids))
            for i in o["items"]:
                units[i["product_id"]] = units.get(i["product_id"], 0) + i["quantity"]
            for a in ids:
                count[a] = count.get(a, 0) + 1
            for x in range(len(ids)):
                for y in range(x + 1, len(ids)):
                    pair[(ids[x], ids[y])] = pair.get((ids[x], ids[y]), 0) + 1
        self._fp, self._baskets, self._count, self._pair, self._units = fp, baskets, count, pair, units

    def together(self, product_id: str, k: int = 3, min_support: int = 2) -> list[dict]:
        self._build()
        n_p, n_all = self._count.get(product_id, 0), len(self._baskets)
        if n_p == 0:
            return []
        out = []
        for (a, b), co in self._pair.items():
            if product_id not in (a, b) or co < min_support:
                continue
            q = b if a == product_id else a
            conf = co / n_p
            lift = conf / (self._count[q] / n_all)
            if lift > 1.0:
                out.append({"product_id": q, "orders": co, "confidence": round(conf, 3), "lift": round(lift, 2)})
        out.sort(key=lambda r: (-(r["confidence"] * r["lift"]), r["product_id"]))
        return out[:k]

    def popularity(self) -> dict[str, int]:
        """Units sold per product (drives the 'Best sellers' sort)."""
        self._build()
        return dict(self._units)

    def order_count(self, product_id: str) -> int:
        self._build()
        return self._count.get(product_id, 0)
