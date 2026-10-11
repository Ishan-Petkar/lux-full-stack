"""Discount coupons: percentage or flat, optional minimum order, category restriction, expiry and usage limit."""
from datetime import datetime, timezone

from pymongo.errors import PyMongoError

from .errors import DatabaseError, ValidationError
from .validators import clean_coupon_code


class CouponService:
    def __init__(self, db):
        self.col = db.coupons

    def get(self, code: str) -> dict | None:
        return self.col.find_one({"_id": clean_coupon_code(code)})

    def evaluate(self, code: str, lines: list[dict]) -> dict:
        """Return {code, discount, label} for a cart, or raise ValidationError explaining why it cannot be used.

        ``lines``: [{"category", "line_total"}]. Discount applies to eligible lines only.
        """
        try:
            c = self.get(code)
        except PyMongoError as exc:
            raise DatabaseError("Could not check the coupon right now.") from exc
        if not c or not c.get("active", True):
            raise ValidationError("This coupon code is not valid.")
        now = datetime.now(timezone.utc)
        exp = c.get("expires_at")
        if exp and (exp.replace(tzinfo=timezone.utc) if exp.tzinfo is None else exp) < now:
            raise ValidationError("This coupon has expired.")
        if c.get("usage_limit") and c.get("used", 0) >= c["usage_limit"]:
            raise ValidationError("This coupon has reached its usage limit.")
        subtotal = sum(l["line_total"] for l in lines)
        if subtotal < c.get("min_order", 0):
            raise ValidationError(f"Add items worth {c['min_order'] - subtotal:,.0f} more to use {c['_id']} "
                                  f"(minimum order {c['min_order']:,.0f}).")
        cats = c.get("categories")
        eligible = sum(l["line_total"] for l in lines if not cats or l["category"] in cats)
        if eligible <= 0:
            raise ValidationError(f"{c['_id']} applies only to: {', '.join(cats)}.")
        discount = eligible * c["value"] / 100 if c["kind"] == "percent" else min(c["value"], eligible)
        if c.get("max_discount"):
            discount = min(discount, c["max_discount"])
        return {"code": c["_id"], "discount": round(discount, 2), "label": c.get("label", c["_id"])}

    def redeem(self, code: str) -> None:
        self.col.update_one({"_id": code}, {"$inc": {"used": 1}})

    def all(self) -> list[dict]:
        return list(self.col.find().sort("_id", 1))

    def create(self, data: dict) -> dict:
        code = clean_coupon_code(data.get("code"))
        kind = data.get("kind")
        if kind not in ("percent", "flat"):
            raise ValidationError("Coupon type must be percent or flat.")
        try:
            value = float(data.get("value"))
        except (TypeError, ValueError):
            raise ValidationError("Coupon value must be a number.") from None
        if value <= 0 or (kind == "percent" and value > 90):
            raise ValidationError("Percent coupons must be between 1 and 90; flat coupons above 0.")
        doc = {"_id": code, "kind": kind, "value": value, "min_order": max(0.0, float(data.get("min_order") or 0)),
               "max_discount": float(data["max_discount"]) if data.get("max_discount") else None,
               "categories": data.get("categories") or None, "label": str(data.get("label") or code)[:80],
               "active": True, "used": 0, "usage_limit": int(data["usage_limit"]) if data.get("usage_limit") else None,
               "expires_at": data.get("expires_at")}
        if self.col.find_one({"_id": code}):
            raise ValidationError(f"Coupon {code} already exists.")
        self.col.insert_one(doc)
        return doc

    def set_active(self, code: str, active: bool) -> None:
        self.col.update_one({"_id": code}, {"$set": {"active": active}})
