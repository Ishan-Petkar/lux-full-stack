import re
JS = """() => [...document.querySelectorAll('figure')].map(f => {
  const img = f.querySelector('img'); const a = f.querySelector('a[href^="/photos/"]'); const u = f.querySelector('a[href^="/@"]');
  const ss = img && (img.getAttribute('srcset') || img.currentSrc || img.src || ''); const src = ss.split(' ')[0].split('?')[0];
  const r = img && img.getBoundingClientRect();
  return {href: a && a.getAttribute('href'), src, alt: img && img.alt, by: u && u.textContent.trim(), user: u && u.getAttribute('href'), ar: r && r.height ? r.width / r.height : 1};
}).filter(x => x.src && x.src.startsWith('https://images.unsplash.com/photo') && x.href)"""
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"


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


