"""Accounts: registration, sign-in (scrypt-hashed passwords), roles and profile."""
import hashlib
import hmac
import os
import uuid
from datetime import datetime, timezone

from pymongo.errors import DuplicateKeyError, PyMongoError

from .errors import AuthError, DatabaseError, NotFoundError, ValidationError
from .validators import clean_email, clean_name, clean_password

_N, _R, _P = 2 ** 14, 8, 1


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=32)
    return f"scrypt${_N}${_R}${_P}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, n, r, p, salt, digest = stored.split("$")
        dk = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=int(n), r=int(r), p=int(p), dklen=32)
        return hmac.compare_digest(dk.hex(), digest)
    except (ValueError, TypeError):
        return False


_DUMMY = hash_password("not-a-real-password-1")     # equalises timing for unknown emails


def _public(user: dict | None) -> dict | None:
    if user is None:
        return None
    return {k: v for k, v in user.items() if k != "password_hash"}


class UserRepository:
    def __init__(self, db):
        self.col = db.users

    def register(self, name: str, email: str, password: str, role: str = "customer") -> dict:
        name, email, password = clean_name(name), clean_email(email), clean_password(password)
        doc = {"_id": f"U-{uuid.uuid4().hex[:8]}", "name": name, "email": email, "role": role,
               "password_hash": hash_password(password), "created_at": datetime.now(timezone.utc)}
        try:
            self.col.insert_one(doc)
        except DuplicateKeyError:
            raise ValidationError("An account with this email already exists. Please sign in.") from None
        except PyMongoError as exc:
            raise DatabaseError("Could not create the account right now. Please try again.") from exc
        return _public(doc)

    def login(self, email: str, password: str) -> dict:
        try:
            email = clean_email(email)
        except ValidationError:
            raise AuthError("Incorrect email or password.") from None
        try:
            user = self.col.find_one({"email": email})
        except PyMongoError as exc:
            raise DatabaseError("Could not sign in right now. Please try again.") from exc
        ok = verify_password(str(password or ""), user.get("password_hash", "") if user else _DUMMY)
        if not user or not ok:
            raise AuthError("Incorrect email or password.")
        return _public(user)

    def get(self, user_id: str) -> dict:
        try:
            user = self.col.find_one({"_id": user_id})
        except PyMongoError as exc:
            raise DatabaseError("Database error while loading the user.") from exc
        if not user:
            raise NotFoundError("User not found.")
        return _public(user)

    def update_name(self, user_id: str, name: str) -> dict:
        self.col.update_one({"_id": user_id}, {"$set": {"name": clean_name(name)}})
        return self.get(user_id)

    def change_password(self, user_id: str, old: str, new: str) -> None:
        user = self.col.find_one({"_id": user_id})
        if not user or not verify_password(str(old or ""), user.get("password_hash", "")):
            raise AuthError("Current password is incorrect.")
        new = clean_password(new)
        if new == old:
            raise ValidationError("Choose a password different from the current one.")
        self.col.update_one({"_id": user_id}, {"$set": {"password_hash": hash_password(new)}})
