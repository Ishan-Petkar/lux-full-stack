import io

import pytest
from PIL import Image

from shop import media
from shop.errors import ValidationError


def png(w=400, h=400, mode="RGB"):
    buf = io.BytesIO()
    Image.new(mode, (w, h), (200, 30, 30) if mode == "RGB" else (200, 30, 30, 0)).save(buf, "PNG")
    return buf.getvalue()


def test_seed_attaches_a_photo_to_every_product(db):
    imgs = [p["image"] for p in db.products.find()]
    assert all(i.startswith("assets/products/") for i in imgs) and len(imgs) == 125
    assert all(media.data_uri(i, 200).startswith("data:image/jpeg;base64,") for i in imgs)


def test_uris_and_unsafe_paths():
    assert media.data_uri("https://example.com/x.jpg") == "https://example.com/x.jpg"
    assert media.data_uri("🛍️") is None and media.data_uri(None) is None
    assert media.data_uri("../../etc/passwd") is None            # cannot escape assets/
    assert media.data_uri("assets/products/NOPE.jpg") is None


def test_upload_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(media, "PRODUCT_DIR", tmp_path)
    rel = media.save_product_image("T-1", png())
    assert rel == "assets/products/T-1.jpg" and (tmp_path / "T-1.jpg").exists()
    assert Image.open(tmp_path / "T-1.jpg").size == (400, 400)


@pytest.mark.parametrize("raw", [b"", b"not an image", b"x" * (5 * 1024 * 1024 + 1), png(100, 100)])
def test_upload_rejected(tmp_path, monkeypatch, raw):
    monkeypatch.setattr(media, "PRODUCT_DIR", tmp_path)
    with pytest.raises(ValidationError):
        media.save_product_image("T-2", raw)


def test_upload_id_sanitised(tmp_path, monkeypatch):
    monkeypatch.setattr(media, "PRODUCT_DIR", tmp_path)
    assert media.save_product_image("../evil", png()) == "assets/products/evil.jpg"
