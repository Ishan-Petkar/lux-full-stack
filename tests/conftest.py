import os
import sys
from pathlib import Path

os.environ.setdefault("USE_MOCK_DB", "true")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mongomock
import pytest

from shop.addresses import AddressService
from shop.bundles import BundleService
from shop.cart import CartService
from shop.catalog import ProductRepository
from shop.coupons import CouponService
from shop.orders import OrderService
from shop.payments import PaymentService
from shop.recommender import RecommenderService
from shop.reviews import ReviewService
from shop.wishlist import WishlistService
from shop.seed_data import seed_if_empty
from shop.users import UserRepository


_REAL = {}


@pytest.fixture()
def db():
    """mongomock by default. Set TEST_MONGO_URI=mongodb://localhost:27017 to run against a real MongoDB: one throw-away
    database is created per test session and its collections are emptied and re-seeded for every test (creating a new
    database per test would create thousands of storage files and can crash a small mongod)."""
    uri = os.getenv("TEST_MONGO_URI")
    if uri:
        import uuid

        from pymongo import MongoClient

        if "db" not in _REAL:
            _REAL["client"] = MongoClient(uri, serverSelectionTimeoutMS=3000)
            _REAL["db"] = _REAL["client"][f"test_{uuid.uuid4().hex[:10]}"]
        database = _REAL["db"]
        for c in database.list_collection_names():
            database[c].delete_many({})
        seed_if_empty(database, force=True)
        yield database
    else:
        database = mongomock.MongoClient()["test_db"]
        seed_if_empty(database)
        yield database


@pytest.fixture(scope="session", autouse=True)
def _drop_real_db():
    yield
    if _REAL.get("db") is not None:
        _REAL["client"].drop_database(_REAL["db"].name)
        _REAL["client"].close()


@pytest.fixture()
def P(db):
    """Resolve a product id from 'Brand Name' (the catalogue is real luxury data, so tests refer to products by name)."""
    def find(label: str) -> str:
        return next(p["_id"] for p in db.products.find() if f"{p['brand']} {p['name']}" == label)
    return find


@pytest.fixture()
def price(db):
    return lambda pid: db.products.find_one({"_id": pid})["price"]


@pytest.fixture()
def repo(db):
    return ProductRepository(db)


@pytest.fixture()
def cart(db):
    return CartService(db)


@pytest.fixture()
def coupons(db):
    return CouponService(db)


@pytest.fixture()
def payments(db):
    return PaymentService(db)


@pytest.fixture()
def orders(db, coupons, payments):
    return OrderService(db, coupons, payments)


@pytest.fixture()
def addresses(db):
    return AddressService(db)


@pytest.fixture()
def wishlist(db):
    return WishlistService(db)


@pytest.fixture()
def reviews(db):
    return ReviewService(db)


@pytest.fixture()
def bundles(db):
    return BundleService(db)


@pytest.fixture()
def users(db):
    return UserRepository(db)


@pytest.fixture()
def reco(repo):
    return RecommenderService(repo)


@pytest.fixture()
def user(users):
    return users.register("Test User", "test@example.com", "Passw0rd!")


@pytest.fixture()
def uid(user):
    return user["_id"]


@pytest.fixture()
def addr(addresses, uid):
    return addresses.add(uid, dict(name="Test User", phone="9876543210", line1="12 Baner Road", city="Pune", state="Maharashtra", pincode="411045"))["_id"]
