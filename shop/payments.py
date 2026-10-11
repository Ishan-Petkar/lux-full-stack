"""Payment gateway: a faithful DEMO of Razorpay's test mode. No real money ever moves.

Flow (same shape as the real Razorpay Standard Checkout integration):
  1. server creates a gateway order            -> create_order
  2. customer pays in the checkout dialog      -> authorize (card / UPI / netbanking) -> optional bank step
  3. gateway returns payment_id + signature    -> HMAC-SHA256(order_id|payment_id, key_secret)
  4. server verifies the signature and amount  -> verify_and_capture  (never trusts the browser)

Test values mirror Razorpay's documented test mode:
  cards  4111 1111 1111 1111 / 5267 3181 8797 5449 / 5104 0155 5555 5558  (any future expiry, any CVV) -> bank page
  UPI    success@razorpay  -> paid        failure@razorpay -> fails
  Netbanking: any listed bank -> bank page with Success / Failure buttons
Card numbers are never stored: only network and last 4 digits.
To go live, implement the same PaymentGateway methods with the `razorpay` SDK and Checkout.js (see README).
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timezone

from pymongo.errors import PyMongoError

from . import config
from .errors import DatabaseError, NotFoundError, PaymentError, ValidationError
from .validators import clean_card, clean_upi

TEST_CARDS = {"4111111111111111", "5267318187975449", "5104015555555558"}
BANKS = ["HDFC Bank", "ICICI Bank", "State Bank of India", "Axis Bank", "Kotak Mahindra Bank", "Punjab National Bank"]


def _token(n: int = 14) -> str:
    return secrets.token_urlsafe(n).replace("-", "A").replace("_", "B")[:n]


class DemoRazorpay:
    name = "Razorpay (demo - test mode)"

    def __init__(self, key_id: str = config.RAZORPAY_KEY_ID, key_secret: str = config.RAZORPAY_KEY_SECRET):
        self.key_id, self._secret = key_id, key_secret

    def create_order(self, amount_paise: int, receipt: str, notes: dict | None = None) -> dict:
        if amount_paise < 100:
            raise PaymentError("Amount must be at least INR 1.00.")
        return {"id": f"order_{_token()}", "entity": "order", "amount": int(amount_paise), "currency": "INR",
                "receipt": receipt, "status": "created", "notes": notes or {}}

    def sign(self, order_id: str, payment_id: str) -> str:
        return hmac.new(self._secret.encode(), f"{order_id}|{payment_id}".encode(), hashlib.sha256).hexdigest()

    def verify(self, order_id: str, payment_id: str, signature: str) -> bool:
        return hmac.compare_digest(self.sign(order_id, payment_id), str(signature or ""))

    def new_payment_id(self) -> str:
        return f"pay_{_token()}"

    def authorize(self, method: str, details: dict) -> dict:
        """Validate the instrument. Returns {"next": "bank"|"paid", "meta": {...}} or raises PaymentError."""
        if method == "card":
            card = clean_card(details.get("number"), details.get("expiry"), details.get("cvv"), details.get("holder"))
            if card["number"] not in TEST_CARDS:
                raise PaymentError("Payment declined by the issuing bank. In demo mode use a Razorpay test card, e.g. 4111 1111 1111 1111.")
            return {"next": "bank", "meta": {"network": card["network"], "last4": card["last4"]}}
        if method == "upi":
            vpa = clean_upi(details.get("vpa"))
            if vpa.lower() == "success@razorpay":
                return {"next": "paid", "meta": {"vpa": "su***@razorpay"}}
            if vpa.lower() == "failure@razorpay":
                raise PaymentError("The UPI payment was declined (demo failure@razorpay).")
            raise PaymentError("Demo mode accepts only success@razorpay (pays) or failure@razorpay (fails).")
        if method == "netbanking":
            if details.get("bank") not in BANKS:
                raise ValidationError("Choose a bank.")
            return {"next": "bank", "meta": {"bank": details["bank"]}}
        raise ValidationError("Choose a payment method.")


class PaymentService:
    def __init__(self, db, gateway: DemoRazorpay | None = None):
        self.col = db.payments
        self.gateway = gateway or DemoRazorpay()

    def _save(self, doc: dict) -> None:
        try:
            self.col.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
        except PyMongoError as exc:
            raise DatabaseError("The payment record could not be saved.") from exc

    def create(self, order: dict) -> dict:
        """Create the gateway order for one of our orders (amount in paise)."""
        paise = int(round(order["total"] * 100))
        rz = self.gateway.create_order(paise, receipt=order["_id"], notes={"order_id": order["_id"]})
        self._save({"_id": rz["id"], "gateway": "razorpay-demo", "order_id": order["_id"], "amount": paise, "currency": "INR",
                    "status": "created", "created_at": datetime.now(timezone.utc)})
        return rz

    def authorize(self, rz_order_id: str, method: str, details: dict) -> dict:
        rec = self.col.find_one({"_id": rz_order_id})
        if not rec or rec["status"] not in ("created", "failed"):
            raise PaymentError("This payment session is no longer valid. Please start again.")
        try:
            res = self.gateway.authorize(method, details)
        except PaymentError as exc:
            self._save({"_id": rz_order_id, "status": "failed", "method": method, "error": str(exc)})
            raise
        self._save({"_id": rz_order_id, "method": method, **{k: v for k, v in res["meta"].items()}})
        if res["next"] == "paid":
            return {"next": "paid", "payment": self._issue(rz_order_id)}
        return {"next": "bank", "payment": None}

    def bank_result(self, rz_order_id: str, success: bool) -> dict:
        if not success:
            self._save({"_id": rz_order_id, "status": "failed", "error": "Payment failed at the bank page (demo)."})
            raise PaymentError("The payment was not authorised by the bank. You can try again.")
        return self._issue(rz_order_id)

    def _issue(self, rz_order_id: str) -> dict:
        pid = self.gateway.new_payment_id()
        sig = self.gateway.sign(rz_order_id, pid)
        self._save({"_id": rz_order_id, "payment_id": pid, "signature": sig, "status": "authorized"})
        return {"razorpay_order_id": rz_order_id, "razorpay_payment_id": pid, "razorpay_signature": sig}

    def verify_and_capture(self, rz_order_id: str, payment_id: str, signature: str, expected_paise: int) -> dict:
        """Server-side verification: signature must match and the amount must equal what we asked for."""
        rec = self.col.find_one({"_id": rz_order_id})
        if not rec:
            raise NotFoundError("Unknown payment session.")
        if not self.gateway.verify(rz_order_id, payment_id, signature) or rec.get("payment_id") != payment_id:
            self._save({"_id": rz_order_id, "status": "failed", "error": "Signature verification failed."})
            raise PaymentError("Payment verification failed. If money was deducted it will be refunded.")
        if rec["amount"] != expected_paise:
            raise PaymentError("Payment amount does not match the order.")
        self._save({"_id": rz_order_id, "status": "captured", "captured_at": datetime.now(timezone.utc)})
        return self.col.find_one({"_id": rz_order_id})

    def refund(self, rz_order_id: str) -> dict:
        rec = self.col.find_one({"_id": rz_order_id})
        if not rec or rec["status"] != "captured":
            raise PaymentError("Only captured payments can be refunded.")
        self._save({"_id": rz_order_id, "status": "refunded", "refund_id": f"rfnd_{_token()}", "refunded_at": datetime.now(timezone.utc)})
        return self.col.find_one({"_id": rz_order_id})
