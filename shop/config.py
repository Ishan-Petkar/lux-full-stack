"""Runtime configuration. Values come from environment variables or a local .env file."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.split(" #")[0].strip())


_load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "product_reco")
USE_MOCK_DB = os.getenv("USE_MOCK_DB", "auto").lower()  # auto | true | false

CURRENCY = "\u20b9"
TOP_N = 4               # default number of recommendations
MAX_LINE_QTY = 10       # max quantity of one product in the cart
MAX_QUERY_LEN = 100

# ---- commerce rules
GST_RATE = 0.18                 # prices are GST-inclusive; the invoice shows the tax portion
FREE_SHIPPING_MIN = 10000       # insured standard delivery is complimentary above this amount
SHIPPING = {"standard": {"label": "Insured standard delivery", "fee": 250, "days": (3, 5)},
            "express": {"label": "Priority insured courier", "fee": 1200, "days": (1, 2)}}
PENDING_PAYMENT_MINUTES = 15    # unpaid online orders are cancelled and their stock released after this
PASSWORD_MIN = 8

# ---- demo payment gateway (mirrors Razorpay test mode; no real money ever moves)
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_curio_demo")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "curio_demo_secret_not_for_production")
MERCHANT_NAME = "curio"
