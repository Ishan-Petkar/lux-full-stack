"""Build review contact sheets of ALL Unsplash candidates per product (.run/up/*.json) -> .run/pick_sheets/sheet_NN.png
Each row: product label + 12 numbered candidates.  Usage: python scripts/pick_sheets.py"""
import io, json, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".run" / ("pick_sheets_sel" if len(sys.argv) > 1 else "pick_sheets"); OUT.mkdir(parents=True, exist_ok=True)
import sys
ONLY = {int(x) for x in sys.argv[1:]}
rows = [r for r in (json.loads(f.read_text()) for f in sorted((ROOT / ".run" / "up").glob("*.json"))) if not ONLY or r["n"] in ONLY]
T, COLS, PER = 138, 12, 7


CACHE = ROOT / ".run" / "thumbs"; CACHE.mkdir(exist_ok=True)


def thumb(item, key=None):
    f = CACHE / f"{key}.jpg" if key else None
    if f and f.exists():
        return Image.open(f).convert("RGB")
    for attempt in range(3):
        try:
            b = requests.get(item["src"] + "?w=220&q=55&fm=jpg&fit=max", timeout=(5, 10)).content
            im = Image.open(io.BytesIO(b)).convert("RGB"); im.thumbnail((T, T))
            if f:
                im.save(f, quality=70)
            return im
        except Exception:
            continue
    return None


def row_thumbs(r):
    ex = ThreadPoolExecutor(12)
    futs = [ex.submit(thumb, c, f"{r['n']}_{i}") for i, c in enumerate(r["cands"][:COLS])]
    out = []
    for f in futs:
        try:
            out.append(f.result(timeout=40))
        except Exception:
            out.append(None)
    ex.shutdown(wait=False, cancel_futures=True)
    return out


for si in range(0, len(rows), PER):
    chunk = rows[si:si + PER]
    sheet = Image.new("RGB", (COLS * (T + 4), len(chunk) * (T + 16)), "white"); d = ImageDraw.Draw(sheet)
    for ri, r in enumerate(chunk):
        y0 = ri * (T + 16)
        d.text((3, y0 + 1), f"#{r['n']}  {r['brand']} - {r['name']}   [{r['mode']}]", fill="black")
        for ci, im in enumerate(row_thumbs(r)):
            if im is None:
                continue
            x = ci * (T + 4) + 2
            sheet.paste(im, (x, y0 + 14)); d.rectangle((x, y0 + 14, x + 17, y0 + 25), fill="red"); d.text((x + 2, y0 + 14), str(ci), fill="white")
        print("row", r["n"], flush=True)
    f = OUT / f"sheet_{si // PER + 1:02d}.png"; sheet.save(f); print(f.name, flush=True)
