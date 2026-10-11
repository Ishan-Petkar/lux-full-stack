"""Download the landing-page campaign photographs (Unsplash License) into assets/hero/ and record credits in .run/hero_credits.json.
Usage: python scripts/fetch_hero.py"""
import io, json
from pathlib import Path
import requests
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
HERO = {"hero.jpg": ("u_ed", "e_coat", 6, 2200), "watch.jpg": ("u_ed", "e_watch", 5, 2200), "bags.jpg": ("u_ed", "e_bag", 0, 1500),
        "jewel.jpg": ("u_ed", "e_jewel", 3, 1500), "scent.jpg": ("u_ed", "e_scent", 5, 2200), "atelier.jpg": ("u_ed", "e_atelier", 4, 2200)}
out = ROOT / "assets" / "hero"; out.mkdir(parents=True, exist_ok=True)
for f in out.glob("*.jpg"):
    f.unlink()
credits = {}
for name, (run, key, idx, w) in HERO.items():
    m = json.loads((ROOT / ".run" / run / key / "meta.json").read_text())[idx]
    im = Image.open(io.BytesIO(requests.get(f"{m['src']}?w={w}&q=82&fm=jpg&fit=max", timeout=60).content)).convert("RGB")
    im.save(out / name, quality=80, optimize=True, progressive=True)
    credits[name] = {"by": m.get("by"), "user": m.get("user"), "href": m["href"], "alt": m.get("alt")}
    print(name, im.size, (m.get("alt") or "")[:50])
(ROOT / ".run" / "hero_credits.json").write_text(json.dumps(credits, indent=1))
