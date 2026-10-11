"""Database access: PyMongo against MongoDB, with an in-memory mongomock fallback."""
import logging

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import PyMongoError

from . import config
from .errors import DatabaseError

log = logging.getLogger(__name__)


def connect():
    """Return (database, backend_label)."""
    mode = config.USE_MOCK_DB
    if mode != "true":
        try:
            client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=2000)
            client.admin.command("ping")
            return client[config.MONGO_DB], "MongoDB"
        except PyMongoError as exc:
            if mode == "false":
                raise DatabaseError(f"Cannot reach MongoDB at {config.MONGO_URI}: {exc}") from exc
            log.warning("MongoDB unreachable (%s); using in-memory mongomock.", exc)
    import mongomock

    return mongomock.MongoClient()[config.MONGO_DB], "mongomock (in-memory)"


def ensure_indexes(db) -> None:
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.products.create_index([("category", ASCENDING)])
    db.carts.create_index([("user_id", ASCENDING)], unique=True)
    db.orders.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    db.orders.create_index([("status", ASCENDING)])
    db.orders.create_index([("items.product_id", ASCENDING)])
    db.reviews.create_index([("product_id", ASCENDING), ("user_id", ASCENDING)], unique=True)
    db.addresses.create_index([("user_id", ASCENDING)])
    db.payments.create_index([("order_id", ASCENDING)])
