"""Stage 4: download the chosen Unsplash photo for every product (scripts/photo_picks.py), normalise it to a 3:4 portrait tile
(900 x 1200) and write assets/products/P###.jpg plus assets/CREDITS.md (photographers, Wikipedia text sources, campaign photos).
Usage: python scripts/fetch_product_photos.py"""
import io, json, sys
from pathlib import Path
import requests
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from photo_picks import FOCUS, PICK  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PROD = ROOT / "assets" / "products"; PROD.mkdir(parents=True, exist_ok=True)
for old in PROD.glob("*.jpg"):
    old.unlink()
cat = {r["id"]: r for r in json.loads((ROOT / "shop" / "catalog_data.json").read_text())}
W, H = 900, 1200


def tile(im: Image.Image, fx: float = .5, fy: float = .5) -> Image.Image:
    w, h = im.size
    target = W / H
    if w / h > target:                                   # too wide: crop sides around the focus
        nw = int(h * target); x = int(min(max(fx * w - nw / 2, 0), w - nw)); im = im.crop((x, 0, x + nw, h))
    else:                                                # too tall: crop top / bottom
        nh = int(w / target); y = int(min(max(fy * h - nh / 2, 0), h - nh)); im = im.crop((0, y, w, y + nh))
    return im.resize((W, H), Image.LANCZOS)


rows = []
for n, idx in sorted(PICK.items()):
    pid = f"P{n:03d}"
    src_n, idx = idx if isinstance(idx, tuple) else (n, idx)          # a pick may borrow a candidate from another product's search
    m = json.loads((ROOT / ".run" / "up" / f"{src_n:03d}.json").read_text())["cands"][idx]
    raw = requests.get(f"{m['src']}?w=1600&q=85&fm=jpg&fit=max", timeout=60).content
    tile(Image.open(io.BytesIO(raw)).convert("RGB"), *FOCUS.get(n, (.5, .5))).save(PROD / f"{pid}.jpg", quality=86, optimize=True, progressive=True)
    rows.append((pid, m))
    print(pid, cat[pid]["brand"], cat[pid]["name"][:28], "|", (m.get("alt") or "")[:48])

hero = json.loads((ROOT / ".run" / "hero_credits.json").read_text()) if (ROOT / ".run" / "hero_credits.json").exists() else {}
out = ["# Credits", "",
       "Everything below is used for illustration in a non-commercial academic project. Brand names are trademarks of their owners; curio is not affiliated with any maison shown.", "",
       "## Product photographs", "",
       "Photographs are from [Unsplash](https://unsplash.com) under the [Unsplash License](https://unsplash.com/license) (free to use; attribution appreciated). "
       "They were selected by searching for each product's brand and model and may show a similar item rather than the exact reference.", "",
       "| Product | Piece | Photographer | Photo |", "|---|---|---|---|"]
for pid, m in rows:
    c = cat[pid]
    out.append(f"| {pid} | {c['brand']} {c['name']} | [{m.get('by') or 'Unsplash contributor'}](https://unsplash.com{m.get('user') or ''}) | [{(m.get('alt') or 'photo')[:60]}](https://unsplash.com{m['href']}) |")
out += ["", "## Campaign photographs (landing page)", "", "| File | Photographer | Photo |", "|---|---|---|"]
for name, m in hero.items():
    out.append(f"| {name} | [{m.get('by') or 'Unsplash contributor'}](https://unsplash.com{m.get('user') or ''}) | [{(m.get('alt') or 'photo')[:60]}](https://unsplash.com{m['href']}) |")
out += ["", "## Product text", "",
        "Descriptions marked *Wikipedia* are the opening sentences of the named English Wikipedia article, licensed [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). "
        "All other descriptions were written for this demo from widely documented public facts. Prices are indicative and rounded; they are not live prices.", "",
        "| Product | Source |", "|---|---|"]
for pid, c in cat.items():
    out.append(f"| {pid} {c['brand']} {c['name']} | {c['source']} |")
(ROOT / "assets" / "CREDITS.md").write_text("\n".join(out) + "\n")
print("done", len(rows))
