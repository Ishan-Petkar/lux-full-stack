"""Price breakdown: subtotal, coupon discount, shipping and the GST already included in prices."""
from . import config
from .errors import ValidationError

METRO_PREFIXES = ("11", "12", "40", "41", "50", "56", "60", "70", "38", "30")


def shipping_options(after_discount: float) -> list[dict]:
    out = []
    for key, o in config.SHIPPING.items():
        free = key == "standard" and after_discount >= config.FREE_SHIPPING_MIN
        out.append({"key": key, "label": o["label"], "fee": 0 if free else o["fee"], "free": free, "days": o["days"]})
    return out


def eta_days(pincode: str | None, method: str) -> tuple[int, int]:
    lo, hi = config.SHIPPING[method]["days"]
    if pincode and not str(pincode).startswith(METRO_PREFIXES):
        lo, hi = lo + 2, hi + 2
    return lo, hi


def quote(subtotal: float, discount: float = 0.0, method: str = "standard") -> dict:
    if method not in config.SHIPPING:
        raise ValidationError("Choose a delivery method.")
    after = round(max(0.0, subtotal - discount), 2)
    fee = next(o["fee"] for o in shipping_options(after) if o["key"] == method)
    return {"subtotal": round(subtotal, 2), "discount": round(discount, 2), "shipping": float(fee), "shipping_method": method,
            "gst_included": round(after * config.GST_RATE / (1 + config.GST_RATE), 2), "total": round(after + fee, 2)}
