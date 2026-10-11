"""Admin dashboard metrics: one pass over the orders collection produces everything the console draws."""
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from .orders import ACTIVE


def _dt(d: datetime) -> datetime:
    return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d


def dashboard(db, include_synthetic: bool = False, days: int = 90) -> dict:
    flt = {} if include_synthetic else {"synthetic": {"$ne": True}}
    orders = list(db.orders.find(flt))
    live = [o for o in orders if o["status"] in ACTIVE]
    now = datetime.now(timezone.utc)
    cur_from, prev_from = now - timedelta(days=days), now - timedelta(days=2 * days)

    by_status: dict[str, int] = defaultdict(int)
    for o in orders:
        by_status[o["status"]] += 1

    units: dict[str, dict] = {}
    cat_rev: dict[str, float] = defaultdict(float)
    brand_rev: dict[str, float] = defaultdict(float)
    pay_split: dict[str, int] = defaultdict(int)
    weekly: dict[str, float] = defaultdict(float)
    daily: dict[str, float] = defaultdict(float)
    heat: dict[tuple[int, int], int] = defaultdict(int)       # (weekday, hour) -> orders
    totals: list[float] = []
    cur = {"revenue": 0.0, "orders": 0}
    prev = {"revenue": 0.0, "orders": 0}
    buyers_cur: set[str] = set()
    buyers_prev: set[str] = set()
    for o in live:
        t = _dt(o["created_at"])
        totals.append(o["total"])
        pay_split["Cash on delivery" if o["payment"]["method"] == "cod" else "Online"] += 1
        heat[(t.weekday(), t.hour)] += 1
        if t >= cur_from:
            cur["revenue"] += o["total"]; cur["orders"] += 1; buyers_cur.add(o["user_id"])
            weekly[f"{(t - timedelta(days=t.weekday())):%Y-%m-%d}"] += o["total"]
            if t >= now - timedelta(days=30):
                daily[f"{t:%Y-%m-%d}"] += o["total"]
        elif t >= prev_from:
            prev["revenue"] += o["total"]; prev["orders"] += 1; buyers_prev.add(o["user_id"])
        for i in o["items"]:
            u = units.setdefault(i["product_id"], {"name": f"{i.get('brand', '')} {i['name']}".strip(), "units": 0, "revenue": 0.0})
            u["units"] += i["quantity"]; u["revenue"] += i["line_total"]
            cat_rev[i.get("category", "Other")] += i["line_total"]
            brand_rev[i.get("brand", "Other")] += i["line_total"]

    revenue = round(sum(totals), 2)
    low = list(db.products.find({"stock": {"$lte": 3}}, {"name": 1, "brand": 1, "stock": 1, "category": 1}).sort("stock", 1))

    def pct(a: float, b: float) -> float | None:
        return round((a - b) / b * 100, 1) if b else None

    return {
        "revenue": revenue, "orders": len(orders), "paid_orders": len(live), "aov": round(revenue / len(live), 2) if live else 0.0,
        "units": sum(u["units"] for u in units.values()), "customers": db.users.count_documents({"role": "customer"}),
        "by_status": dict(by_status), "daily": dict(sorted(daily.items())), "weekly": dict(sorted(weekly.items())),
        "top_products": sorted(units.items(), key=lambda kv: -kv[1]["revenue"])[:10],
        "category_revenue": dict(sorted(cat_rev.items(), key=lambda kv: -kv[1])),
        "brand_revenue": dict(sorted(brand_rev.items(), key=lambda kv: -kv[1])[:10]),
        "payment_split": dict(pay_split), "order_values": totals, "heatmap": dict(heat), "low_stock": low,
        "period_days": days, "current": cur, "previous": prev,
        "delta_revenue": pct(cur["revenue"], prev["revenue"]), "delta_orders": pct(cur["orders"], prev["orders"]),
        "delta_aov": pct(cur["revenue"] / cur["orders"] if cur["orders"] else 0, prev["revenue"] / prev["orders"] if prev["orders"] else 0),
        "active_buyers": len(buyers_cur), "repeat_rate": round(100 * len(buyers_cur & buyers_prev) / len(buyers_prev), 1) if buyers_prev else None,
        "inventory_value": round(sum(p["price"] * p["stock"] for p in db.products.find({}, {"price": 1, "stock": 1})), 2),
    }
