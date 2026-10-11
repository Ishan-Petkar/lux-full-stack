"""Stage 1 (photo sourcing): browse Unsplash search pages in headless Chrome, collect candidate photos and build
numbered contact sheets for review.   Usage: python scripts/unsplash_candidates.py groups.json outdir"""
import io, json, sys, time
from pathlib import Path
import requests
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
groups = json.loads((ROOT / "scripts" / sys.argv[1]).read_text())
OUT = ROOT / ".run" / sys.argv[2]; OUT.mkdir(parents=True, exist_ok=True)
N = int(sys.argv[3]) if len(sys.argv) > 3 else 12
JS = """() => [...document.querySelectorAll('figure')].map(f => {
  const img = f.querySelector('img'); const a = f.querySelector('a[href^="/photos/"]'); const u = f.querySelector('a[href^="/@"]');
  const ss = img && (img.getAttribute('srcset') || img.currentSrc || img.src || '');
  const src = ss.split(' ')[0].split('?')[0];
  return {href: a && a.getAttribute('href'), src, alt: img && img.alt, by: u && u.textContent.trim(), user: u && u.getAttribute('href')};
}).filter(x => x.src && x.src.startsWith('https://images.unsplash.com/photo') && x.href)"""

rowsets = []
with sync_playwright() as pw:
    br = pw.chromium.launch(channel="chrome", headless=True)
    ctx = br.new_context(viewport={"width": 1400, "height": 1000}, user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
    page = ctx.new_page()
    for key, q in groups.items():
        slug = q.replace(" ", "-")
        for attempt in range(3):
            page.goto(f"https://unsplash.com/s/photos/{slug}", wait_until="domcontentloaded")
            try:
                page.wait_for_selector("figure img", timeout=20000); break
            except Exception:
                print("retry", key, attempt)
        page.wait_for_timeout(1500)
        for _ in range(3):
            page.mouse.wheel(0, 1500); page.wait_for_timeout(700)
        seen, items = set(), []
        for it in page.evaluate(JS):
            if it["src"] not in seen:
                seen.add(it["src"]); items.append(it)
            if len(items) >= N:
                break
        d = OUT / key; d.mkdir(exist_ok=True)
        (d / "meta.json").write_text(json.dumps(items, indent=1))
        rowsets.append((key, q, items))
    br.close()

COLS, T = 12, 150
for si in range(0, len(rowsets), 6):
    chunk = rowsets[si:si + 6]
    sheet = Image.new("RGB", (COLS * (T + 6), len(chunk) * (T + 22)), "white"); dr = ImageDraw.Draw(sheet)
    for ri, (key, q, items) in enumerate(chunk):
        y0 = ri * (T + 22)
        dr.text((4, y0 + 2), f"{key}  -  {q}", fill="black")
        for i, it in enumerate(items[:COLS]):
            try:
                b = requests.get(it["src"] + "?w=240&q=60&fm=jpg&fit=crop", timeout=30).content
                im = Image.open(io.BytesIO(b)).convert("RGB"); im.thumbnail((T, T))
                x = i * (T + 6) + 3
                sheet.paste(im, (x, y0 + 18)); dr.rectangle((x, y0 + 18, x + 20, y0 + 31), fill="red"); dr.text((x + 3, y0 + 19), str(i), fill="white")
            except Exception as e:
                print("skip", key, i, e)
    f = OUT / f"sheet_{si // 6 + 1:02d}.png"; sheet.save(f); print("sheet", f.name, [k for k, *_ in chunk])
