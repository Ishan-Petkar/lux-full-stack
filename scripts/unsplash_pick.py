"""Stage 2: for every catalogue product search Unsplash for the exact brand + model, score results by how well the photo's
description matches the brand / model words, and save the top candidates (.run/up/<n>.json) for review.
Usage: python scripts/unsplash_pick.py [start] [end]   (1-based, inclusive)"""
import json, re, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog_master import MASTER  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".run" / "up"; OUT.mkdir(parents=True, exist_ok=True)
start = int(sys.argv[1]) if len(sys.argv) > 1 else 1
end = int(sys.argv[2]) if len(sys.argv) > 2 else len(MASTER)
JS = """() => [...document.querySelectorAll('figure')].map(f => {
  const img = f.querySelector('img'); const a = f.querySelector('a[href^="/photos/"]'); const u = f.querySelector('a[href^="/@"]');
  const ss = img && (img.getAttribute('srcset') || img.currentSrc || img.src || ''); const src = ss.split(' ')[0].split('?')[0];
  const r = img && img.getBoundingClientRect();
  return {href: a && a.getAttribute('href'), src, alt: img && img.alt, by: u && u.textContent.trim(), user: u && u.getAttribute('href'), ar: r && r.height ? r.width / r.height : 1};
}).filter(x => x.src && x.src.startsWith('https://images.unsplash.com/photo') && x.href)"""
STOP = {"the", "de", "and", "classic", "original", "eau", "parfum", "toilette", "pro", "professional", "bag", "watch"}


def tokens(*parts):
    return [w for w in re.findall(r"[a-zà-ÿ0-9]+", " ".join(parts).lower()) if len(w) > 2 and w not in STOP]


def search(page, q):
    slug = re.sub(r"[^A-Za-z0-9]+", "-", q).strip("-")
    for attempt in range(3):
        page.goto(f"https://unsplash.com/s/photos/{slug}", wait_until="domcontentloaded")
        try:
            page.wait_for_selector("figure img", timeout=20000); break
        except Exception:
            pass
    page.wait_for_timeout(1200)
    seen, items = set(), []
    for it in page.evaluate(JS):
        if it["src"] not in seen:
            seen.add(it["src"]); items.append(it)
    return items


with sync_playwright() as pw:
    br = pw.chromium.launch(channel="chrome", headless=True)
    ctx = br.new_context(viewport={"width": 1400, "height": 1000}, user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
    page = ctx.new_page()
    for n in range(start, end + 1):
        brand, name, wiki, cat, sub, price, stock, tags, fb = MASTER[n - 1]
        items = search(page, f"{brand} {name}")
        bt, nt = tokens(brand), tokens(name)
        for it in items:
            alt = (it["alt"] or "").lower()
            it["score"] = 2 * sum(t in alt for t in bt) + sum(t in alt for t in nt)
        ranked = sorted(items, key=lambda x: -x["score"])
        mode = "exact"
        if not ranked or ranked[0]["score"] == 0:
            items = search(page, fb); ranked = items; mode = "generic"
            for it in ranked:
                it["score"] = 0
        (OUT / f"{n:03d}.json").write_text(json.dumps({"n": n, "brand": brand, "name": name, "mode": mode, "cands": ranked[:12]}, indent=1))
        top = ranked[0] if ranked else {}
        print(f"{n:3d} {brand} {name[:28]:28s} {mode:7s} score={top.get('score')} alt={(top.get('alt') or '')[:60]}", flush=True)
    br.close()
