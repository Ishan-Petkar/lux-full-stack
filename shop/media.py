"""Product images: resolve a product's `image` field to a displayable data URI and save admin uploads."""
import base64
import io
from functools import lru_cache
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from . import config
from .errors import ValidationError

PRODUCT_DIR = config.ROOT / "assets" / "products"
MAX_UPLOAD = 5 * 1024 * 1024


def image_path(ref: str | None) -> Path | None:
    """Local file for an `image` value such as 'assets/products/P001.jpg' (None for URLs / emoji / missing)."""
    if not ref or ref.startswith(("http://", "https://")) or "/" not in ref:
        return None
    p = (config.ROOT / ref).resolve()
    try:
        p.relative_to(config.ROOT / "assets")      # never serve files from outside assets/
    except ValueError:
        return None
    return p if p.is_file() else None


@lru_cache(maxsize=1024)
def _encode(path: str, mtime: float, size: int) -> str:
    im = Image.open(path).convert("RGB")
    im.thumbnail((size, size))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=82, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def data_uri(ref: str | None, size: int = 640) -> str | None:
    """Data URI (or the URL itself) for an image reference; None if it is an emoji / missing file."""
    if ref and ref.startswith(("http://", "https://")):
        return ref
    p = image_path(ref)
    if not p:
        return None
    try:
        return _encode(str(p), p.stat().st_mtime, size)
    except (OSError, UnidentifiedImageError):
        return None


def save_product_image(product_id: str, raw: bytes) -> str:
    """Validate an uploaded image, store it as assets/products/<id>.jpg and return the relative path."""
    if not raw:
        raise ValidationError("No image data received.")
    if len(raw) > MAX_UPLOAD:
        raise ValidationError("Image is larger than 5 MB.")
    try:
        probe = Image.open(io.BytesIO(raw))
        probe.verify()
        im = Image.open(io.BytesIO(raw))
        fmt = (im.format or "").upper()
    except (UnidentifiedImageError, OSError):
        raise ValidationError("That file is not a valid image (use JPG, PNG or WebP).") from None
    if fmt not in ("JPEG", "PNG", "WEBP"):
        raise ValidationError("Use a JPG, PNG or WebP image.")
    if min(im.size) < 200:
        raise ValidationError("Image is too small (minimum 200 px on the short side).")
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        base = Image.new("RGB", im.size, (244, 242, 238))
        base.paste(im, mask=im.split()[-1])
        im = base
    im = im.convert("RGB")
    im.thumbnail((1200, 1200))
    PRODUCT_DIR.mkdir(parents=True, exist_ok=True)
    safe = "".join(c for c in product_id if c.isalnum() or c in "-_")
    im.save(PRODUCT_DIR / f"{safe}.jpg", quality=86, optimize=True)
    return f"assets/products/{safe}.jpg"
