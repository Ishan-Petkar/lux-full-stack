"""Re-search products whose first search returned too few photos, using a plain descriptive query. Overwrites .run/up/<n>.json."""
import json, re, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog_master import MASTER  # noqa: E402
import unsplash_pick_lib as lib  # noqa: E402

Q = {25: "leather duffle bag luxury", 19: "quilted chain handbag", 20: "monogram handbag", 21: "black leather top handle handbag", 3: "rectangular watch", 16: "chronograph watch", 20: "monogram handbag", 32: "perfume bottle", 38: "cologne bottle", 40: "cologne bottle men",
     44: "browline sunglasses", 45: "tortoiseshell sunglasses", 51: "gold snake bracelet", 60: "camel overcoat", 62: "cashmere turtleneck",
     63: "silk scarf", 89: "lighter", 92: "luxury steel watch", 94: "pilot watch", 97: "quilted chain bag", 98: "woven leather bag",
     100: "black chain shoulder bag", 104: "perfume bottle gold", 110: "diamond pendant necklace", 111: "gold ring", 119: "studded pump heels", 121: "leather ankle boots"}
ROOT = Path(__file__).resolve().parent.parent
with sync_playwright() as pw:
    br = pw.chromium.launch(channel="chrome", headless=True)
    ctx = br.new_context(viewport={"width": 1400, "height": 1000}, user_agent=lib.UA)
    page = ctx.new_page()
    done = {int(l.split()[0]) for l in (ROOT / '.run' / 'retry.log').read_text().splitlines() if l[:1].isdigit()} if False else set()
    for n, q in Q.items():
        if (ROOT / '.run' / 'up' / f'{n:03d}.json').exists() and json.loads((ROOT / '.run' / 'up' / f'{n:03d}.json').read_text()).get('mode') == 'retry':
            continue
        brand, name = MASTER[n - 1][0], MASTER[n - 1][1]
        try:
            items = lib.search(page, q)
        except Exception as e:
            print('ERR', n, e, flush=True); continue
        (ROOT / ".run" / "up" / f"{n:03d}.json").write_text(json.dumps({"n": n, "brand": brand, "name": name, "mode": "retry", "cands": items[:12]}, indent=1))
        print(n, brand, name, len(items), flush=True)
    br.close()
