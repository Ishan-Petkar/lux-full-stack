"""Input validation. Every function returns the cleaned value or raises ValidationError."""
import re

from . import config
from .errors import ValidationError

_EMAIL = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")
_NAME = re.compile(r"^[A-Za-z][A-Za-z .'-]{1,59}$")


def clean_name(value) -> str:
    value = " ".join(str(value or "").split())
    if not _NAME.match(value):
        raise ValidationError("Name must be 2-60 letters (spaces, . ' - allowed) and start with a letter.")
    return value


def clean_email(value) -> str:
    value = str(value or "").strip().lower()
    if len(value) > 120 or not _EMAIL.match(value):
        raise ValidationError("Please enter a valid email address, e.g. name@example.com.")
    return value


def clean_query(value) -> str:
    value = " ".join(str(value or "").split())
    if len(value) > config.MAX_QUERY_LEN:
        raise ValidationError(f"Search text is limited to {config.MAX_QUERY_LEN} characters.")
    return value


def clean_quantity(value, maximum: int = config.MAX_LINE_QTY) -> int:
    if isinstance(value, bool) or isinstance(value, float) and not float(value).is_integer():
        raise ValidationError("Quantity must be a whole number.")
    try:
        qty = int(value)
    except (TypeError, ValueError):
        raise ValidationError("Quantity must be a whole number.") from None
    if qty < 1:
        raise ValidationError("Quantity must be at least 1.")
    if qty > maximum:
        raise ValidationError(f"You can order at most {maximum} units of one product.")
    return qty


def clean_product(data: dict) -> dict:
    """Validate a product form / import row and return a normalised document (without _id)."""
    def text(key, label, lo, hi, required=True):
        v = " ".join(str(data.get(key) or "").split())
        if not v and not required:
            return ""
        if not (lo <= len(v) <= hi):
            raise ValidationError(f"{label} is required ({lo}-{hi} characters).")
        return v

    name = text("name", "Product name", 2, 120)
    category = text("category", "Category", 2, 60)
    brand = text("brand", "Brand", 1, 60)
    description = text("description", "Description", 10, 1000)
    subcategory = text("subcategory", "Subcategory", 0, 60, required=False)
    image = text("image", "Image", 0, 300, required=False) or ""

    try:
        price = round(float(data.get("price")), 2)
    except (TypeError, ValueError):
        raise ValidationError("Price must be a number.") from None
    if not 0 < price <= 10_000_000:
        raise ValidationError("Price must be greater than 0.")

    try:
        stock_f = float(data.get("stock"))
    except (TypeError, ValueError):
        raise ValidationError("Stock must be a whole number.") from None
    if not stock_f.is_integer() or stock_f < 0 or stock_f > 100_000:
        raise ValidationError("Stock must be a whole number between 0 and 100000.")

    tags = data.get("tags") or []
    if isinstance(tags, str):
        tags = tags.split(",")
    tags = sorted({t.strip().lower() for t in tags if t and t.strip()})
    if any(len(t) > 40 for t in tags) or len(tags) > 20:
        raise ValidationError("Use at most 20 tags of up to 40 characters each.")

    return {
        "name": name, "description": description, "category": category,
        "subcategory": subcategory, "brand": brand, "price": price,
        "image": image, "stock": int(stock_f), "tags": tags,
    }


# ---------------------------------------------------------------- accounts, addresses, payments, reviews
_PHONE = re.compile(r"^[6-9]\d{9}$")
_PIN = re.compile(r"^[1-9]\d{5}$")
_UPI = re.compile(r"^[A-Za-z0-9._-]{2,256}@[A-Za-z]{2,64}$")
_COUPON = re.compile(r"^[A-Z0-9]{3,20}$")


def clean_password(value) -> str:
    value = str(value or "")
    if len(value) < config.PASSWORD_MIN or len(value) > 128:
        raise ValidationError(f"Password must be {config.PASSWORD_MIN}-128 characters.")
    if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
        raise ValidationError("Password must contain at least one letter and one number.")
    return value


def clean_phone(value) -> str:
    digits = re.sub(r"[\s-]", "", str(value or "")).removeprefix("+91")
    if not _PHONE.match(digits):
        raise ValidationError("Enter a valid 10-digit Indian mobile number.")
    return digits


def clean_pincode(value) -> str:
    value = str(value or "").strip()
    if not _PIN.match(value):
        raise ValidationError("Enter a valid 6-digit PIN code.")
    return value


def clean_address(data: dict) -> dict:
    def text(key, label, lo, hi, required=True):
        v = " ".join(str(data.get(key) or "").split())
        if not v and not required:
            return ""
        if not (lo <= len(v) <= hi):
            raise ValidationError(f"{label} is required ({lo}-{hi} characters).")
        return v

    return {"label": text("label", "Address label", 0, 30, required=False) or "Home",
            "name": clean_name(data.get("name")), "phone": clean_phone(data.get("phone")),
            "line1": text("line1", "Address line 1", 5, 120), "line2": text("line2", "Address line 2", 0, 120, required=False),
            "city": text("city", "City", 2, 60), "state": text("state", "State", 2, 60), "pincode": clean_pincode(data.get("pincode"))}


def clean_coupon_code(value) -> str:
    value = str(value or "").strip().upper()
    if not _COUPON.match(value):
        raise ValidationError("Coupon codes use 3-20 letters or numbers.")
    return value


def clean_review(rating, title, body) -> tuple[int, str, str]:
    try:
        rating = int(rating)
    except (TypeError, ValueError):
        raise ValidationError("Choose a rating from 1 to 5.") from None
    if not 1 <= rating <= 5:
        raise ValidationError("Choose a rating from 1 to 5.")
    title = " ".join(str(title or "").split())
    body = " ".join(str(body or "").split())
    if not 2 <= len(title) <= 80:
        raise ValidationError("Review title must be 2-80 characters.")
    if not 10 <= len(body) <= 1500:
        raise ValidationError("Review text must be 10-1500 characters.")
    return rating, title, body


def clean_upi(value) -> str:
    value = str(value or "").strip()
    if not _UPI.match(value):
        raise ValidationError("Enter a valid UPI ID, e.g. name@bank.")
    return value


def luhn_ok(number: str) -> bool:
    digits = [int(c) for c in number][::-1]
    return sum(d if i % 2 == 0 else (d * 2 - 9 if d * 2 > 9 else d * 2) for i, d in enumerate(digits)) % 10 == 0


def clean_card(number, expiry, cvv, holder) -> dict:
    n = re.sub(r"[\s-]", "", str(number or ""))
    if not n.isdigit() or not 13 <= len(n) <= 19 or not luhn_ok(n):
        raise ValidationError("Card number is invalid.")
    m = re.match(r"^(0[1-9]|1[0-2])\s*/\s*(\d{2})$", str(expiry or "").strip())
    if not m:
        raise ValidationError("Enter expiry as MM/YY.")
    from datetime import date
    yy, mm = 2000 + int(m.group(2)), int(m.group(1))
    today = date.today()
    if (yy, mm) < (today.year, today.month):
        raise ValidationError("This card has expired.")
    if not re.match(r"^\d{3,4}$", str(cvv or "")):
        raise ValidationError("Enter the 3 or 4 digit CVV.")
    return {"number": n, "last4": n[-4:], "network": "Visa" if n[0] == "4" else "Mastercard" if n[0] == "5" else "Card",
            "holder": clean_name(holder)}
