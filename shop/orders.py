"""Order Management: checkout, payment confirmation, tracking, cancellation and refunds.

Lifecycle:  Pending Payment -> Placed -> Packed -> Shipped -> Delivered        (Cancelled from Pending/Placed/Packed)
Stock is reserved atomically (conditional $inc) when the order is created and released on cancellation / expiry.
"""
import uuid
from datetime import datetime, timedelta, timezone

from pymongo.errors import PyMongoError

from . import config, pricing
from .errors import AuthError, DatabaseError, NotFoundError, PaymentError, StockError, ValidationError

STATUS_FLOW = {"Placed": "Packed", "Packed": "Shipped", "Shipped": "Delivered"}
ACTIVE = ["Placed", "Packed", "Shipped", "Delivered"]


def _now():
    return datetime.now(timezone.utc)


def require_admin(user: dict | None) -> None:
    if not user or user.get("role") != "admin":
        raise AuthError("This action needs an administrator account.")


class OrderService:
    def __init__(self, db, coupons, payments):
        self.orders, self.products, self.carts, self.addresses = db.orders, db.products, db.carts, db.addresses
        self.coupons, self.payments = coupons, payments

    # ------------------------------------------------------------------ create
    def create(self, user_id: str, address_id: str, shipping_method: str = "standard", coupon_code: str | None = None,
               payment_method: str = "razorpay") -> dict:
        if payment_method not in ("razorpay", "cod"):
            raise ValidationError("Choose a payment method.")
        try:
            cart = self.carts.find_one({"_id": user_id})
            items = cart["items"] if cart else []
            if not items:
                raise ValidationError("Your bag is empty.")
            addr = self.addresses.find_one({"_id": address_id, "user_id": user_id})
            if not addr:
                raise ValidationError("Choose a delivery address.")

            lines = []
            for item in items:
                p = self.products.find_one({"_id": item["product_id"]})
                if not p:
                    raise ValidationError("A product in your bag is no longer available. Please remove it.")
                if p["stock"] < item["quantity"]:
                    raise StockError(f"Only {p['stock']} unit(s) of '{p['name']}' left; please reduce the quantity.")
                lines.append({"product_id": p["_id"], "name": p["name"], "brand": p["brand"], "category": p["category"],
                              "unit_price": p["price"], "quantity": item["quantity"],
                              "line_total": round(p["price"] * item["quantity"], 2), "image": p.get("image", "")})
            coupon = self.coupons.evaluate(coupon_code, lines) if coupon_code else None
            subtotal = round(sum(l["line_total"] for l in lines), 2)
            price = pricing.quote(subtotal, coupon["discount"] if coupon else 0.0, shipping_method)
            if payment_method == "cod" and price["total"] > 50000:
                raise ValidationError("Cash on delivery is available for orders up to 50,000. Please pay online.")

            reserved = []
            try:
                for ln in lines:
                    r = self.products.update_one({"_id": ln["product_id"], "stock": {"$gte": ln["quantity"]}},
                                                 {"$inc": {"stock": -ln["quantity"]}})
                    if r.modified_count != 1:
                        raise StockError(f"'{ln['name']}' just went out of stock. Please review your bag.")
                    reserved.append(ln)
                now = _now()
                status = "Pending Payment" if payment_method == "razorpay" else "Placed"
                order = {
                    "_id": f"ORD-{now:%Y%m%d}-{uuid.uuid4().hex[:6].upper()}", "user_id": user_id, "items": lines,
                    "pricing": {**price, "coupon_code": coupon["code"] if coupon else None},
                    "total": price["total"],
                    "address": {k: addr[k] for k in ("label", "name", "phone", "line1", "line2", "city", "state", "pincode")},
                    "payment": {"method": payment_method, "status": "pending"}, "status": status,
                    "timeline": [{"status": status, "at": now, "note": "Order created" if payment_method == "razorpay" else "Order placed (cash on delivery)"}],
                    "created_at": now, "updated_at": now,
                }
                self.orders.insert_one(order)
            except Exception:
                for ln in reserved:
                    self.products.update_one({"_id": ln["product_id"]}, {"$inc": {"stock": ln["quantity"]}})
                raise
            self.carts.update_one({"_id": user_id}, {"$set": {"items": []}})
            if payment_method == "cod" and coupon:
                self.coupons.redeem(coupon["code"])
            return order
        except PyMongoError as exc:
            raise DatabaseError("The order could not be saved. Your order was not placed; please try again.") from exc

    # ------------------------------------------------------------------ payment
    def _load(self, order_id: str, user_id: str | None = None) -> dict:
        o = self.orders.find_one({"_id": order_id} if user_id is None else {"_id": order_id, "user_id": user_id})
        if not o:
            raise NotFoundError("Order not found.")
        return o

    def start_payment(self, order_id: str, user_id: str) -> dict:
        o = self._load(order_id, user_id)
        if o["status"] != "Pending Payment":
            raise PaymentError("This order is not awaiting payment.")
        age = _now() - o["created_at"].replace(tzinfo=timezone.utc)
        if age > timedelta(minutes=config.PENDING_PAYMENT_MINUTES):
            self.cancel(order_id, user_id, note="Payment window expired")
            raise PaymentError("The payment window expired and the order was cancelled. Please place it again.")
        rz = self.payments.create(o)
        self.orders.update_one({"_id": order_id}, {"$set": {"payment.gateway_order_id": rz["id"], "updated_at": _now()}})
        return rz

    def confirm_payment(self, order_id: str, user_id: str, result: dict) -> dict:
        o = self._load(order_id, user_id)
        if o["status"] != "Pending Payment":
            raise PaymentError("This order is not awaiting payment.")
        if result.get("razorpay_order_id") != o["payment"].get("gateway_order_id"):
            raise PaymentError("Payment does not belong to this order.")
        rec = self.payments.verify_and_capture(result["razorpay_order_id"], result["razorpay_payment_id"],
                                               result["razorpay_signature"], int(round(o["total"] * 100)))
        now = _now()
        self.orders.update_one({"_id": order_id}, {
            "$set": {"status": "Placed", "payment.status": "paid", "payment.payment_id": result["razorpay_payment_id"],
                     "payment.network": rec.get("network"), "payment.last4": rec.get("last4"), "payment.bank": rec.get("bank"),
                     "payment.method_used": rec.get("method"), "updated_at": now},
            "$push": {"timeline": {"status": "Placed", "at": now, "note": "Payment received"}}})
        if o["pricing"].get("coupon_code"):
            self.coupons.redeem(o["pricing"]["coupon_code"])
        return self._load(order_id)

    def payment_failed(self, order_id: str, reason: str) -> None:
        now = _now()
        self.orders.update_one({"_id": order_id, "status": "Pending Payment"},
                               {"$set": {"payment.status": "failed", "updated_at": now},
                                "$push": {"timeline": {"status": "Pending Payment", "at": now, "note": f"Payment failed: {reason}"[:200]}}})

    # ------------------------------------------------------------------ lifecycle
    def cancel(self, order_id: str, user_id: str | None, note: str = "Cancelled by customer") -> dict:
        o = self._load(order_id, user_id)
        if o["status"] not in ("Pending Payment", "Placed", "Packed"):
            raise ValidationError("This order can no longer be cancelled.")
        for ln in o["items"]:
            self.products.update_one({"_id": ln["product_id"]}, {"$inc": {"stock": ln["quantity"]}})
        pay = dict(o["payment"])
        note_extra = ""
        if pay.get("status") == "paid" and pay.get("gateway_order_id"):
            self.payments.refund(pay["gateway_order_id"])
            pay["status"] = "refunded"
            note_extra = " - refund initiated"
        now = _now()
        self.orders.update_one({"_id": order_id}, {
            "$set": {"status": "Cancelled", "payment": pay, "updated_at": now},
            "$push": {"timeline": {"status": "Cancelled", "at": now, "note": note + note_extra}}})
        return self._load(order_id)

    def set_status(self, order_id: str, new_status: str, actor: dict) -> dict:
        require_admin(actor)
        o = self._load(order_id)
        if STATUS_FLOW.get(o["status"]) != new_status:
            raise ValidationError(f"An order that is '{o['status']}' cannot move to '{new_status}'.")
        now = _now()
        upd = {"status": new_status, "updated_at": now}
        if new_status == "Delivered" and o["payment"]["method"] == "cod":
            upd["payment.status"] = "paid"
        self.orders.update_one({"_id": order_id}, {"$set": upd, "$push": {"timeline": {"status": new_status, "at": now, "note": f"Updated by {actor['name']}"}}})
        return self._load(order_id)

    def expire_pending(self, minutes: int = config.PENDING_PAYMENT_MINUTES) -> int:
        cutoff = _now() - timedelta(minutes=minutes)
        n = 0
        for o in list(self.orders.find({"status": "Pending Payment"})):
            if o["created_at"].replace(tzinfo=timezone.utc) < cutoff:
                self.cancel(o["_id"], None, note="Payment window expired")
                n += 1
        return n

    # ------------------------------------------------------------------ reads
    def get(self, order_id: str, user_id: str | None = None) -> dict:
        return self._load(order_id, user_id)

    def history(self, user_id: str) -> list[dict]:
        try:
            return list(self.orders.find({"user_id": user_id}).sort("created_at", -1))
        except PyMongoError as exc:
            raise DatabaseError("Could not load your orders. Please try again.") from exc

    def all(self, include_synthetic: bool = False, limit: int = 300) -> list[dict]:
        flt = {} if include_synthetic else {"synthetic": {"$ne": True}}
        return list(self.orders.find(flt).sort("created_at", -1).limit(limit))
