"""Saved delivery addresses (address book)."""
import uuid

from pymongo.errors import PyMongoError

from .errors import DatabaseError, NotFoundError
from .validators import clean_address


class AddressService:
    def __init__(self, db):
        self.col = db.addresses

    def list(self, user_id: str) -> list[dict]:
        try:
            return list(self.col.find({"user_id": user_id}).sort([("is_default", -1), ("_id", 1)]))
        except PyMongoError as exc:
            raise DatabaseError("Could not load your addresses.") from exc

    def get(self, user_id: str, address_id: str) -> dict:
        a = self.col.find_one({"_id": address_id, "user_id": user_id})
        if not a:
            raise NotFoundError("That address no longer exists.")
        return a

    def add(self, user_id: str, data: dict) -> dict:
        doc = clean_address(data)
        doc.update({"_id": f"A-{uuid.uuid4().hex[:8]}", "user_id": user_id,
                    "is_default": self.col.count_documents({"user_id": user_id}) == 0})
        try:
            self.col.insert_one(doc)
        except PyMongoError as exc:
            raise DatabaseError("Could not save the address.") from exc
        return doc

    def update(self, user_id: str, address_id: str, data: dict) -> dict:
        self.get(user_id, address_id)
        self.col.update_one({"_id": address_id}, {"$set": clean_address(data)})
        return self.get(user_id, address_id)

    def delete(self, user_id: str, address_id: str) -> None:
        a = self.get(user_id, address_id)
        self.col.delete_one({"_id": address_id})
        if a["is_default"]:
            nxt = self.col.find_one({"user_id": user_id})
            if nxt:
                self.col.update_one({"_id": nxt["_id"]}, {"$set": {"is_default": True}})

    def set_default(self, user_id: str, address_id: str) -> None:
        self.get(user_id, address_id)
        self.col.update_many({"user_id": user_id}, {"$set": {"is_default": False}})
        self.col.update_one({"_id": address_id}, {"$set": {"is_default": True}})
