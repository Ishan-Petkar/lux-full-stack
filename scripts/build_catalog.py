"""Stage 1: enrich scripts/catalog_master.py with REAL data from Wikipedia / Wikimedia Commons.

For every product with a Wikipedia title: real extract (description), page URL, and the article's lead photo if it has a free licence
and is at least 700 px. Output: .run/catalog_stage1.json + raw photos in .run/wiki/<n>.jpg  (reviewed before stage 2 normalises them).
Usage: python scripts/build_catalog.py
"""
import html, json, re, sys, time
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog_master import MASTER  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / ".run" / "wiki"; RAW.mkdir(parents=True, exist_ok=True)
H = {"User-Agent": "CurioMCAProject/1.0 (academic project; ishanpetkar@gmail.com)"}
API = "https://en.wikipedia.org/w/api.php"
FREE = ("cc", "public domain", "pd", "gfdl", "attribution", "free art", "copyrighted free")


def q(**p):
    for a in range(4):
        r = requests.get(API, params={"format": "json", "formatversion": 2, **p}, headers=H, timeout=40)
        if r.status_code == 429:
            time.sleep(3 * (a + 1)); continue
        r.raise_for_status(); return r.json()
    raise RuntimeError("rate limited")


def sentences(text, limit=300):
    text = re.sub(r"\s+", " ", re.sub(r"\s*\([^()]*\)", "", text or "")).strip()
    out = ""
    for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text):
        if len(out) + len(s) > limit and out:
            break
        out = (out + " " + s).strip()
    return out


def lookup(title):
    d = q(action="query", titles=title, redirects=1, prop="extracts|pageimages|info", exintro=1, explaintext=1, piprop="name|original", inprop="url")
    pg = (d["query"]["pages"] or [{}])[0]
    if pg.get("missing"):
        return None
    info = {"wiki": pg["title"], "url": pg.get("fullurl"), "extract": sentences(pg.get("extract", "")), "file": pg.get("pageimage"),
            "orig": (pg.get("original") or {}).get("source"), "w": (pg.get("original") or {}).get("width", 0), "h": (pg.get("original") or {}).get("height", 0)}
    if info["file"]:
        fi = q(action="query", titles="File:" + info["file"], prop="imageinfo", iiprop="extmetadata|mime")
        ii = ((fi["query"]["pages"][0].get("imageinfo") or [{}])[0])
        ex = ii.get("extmetadata", {})
        info["license"] = (ex.get("LicenseShortName", {}) or {}).get("value", "")
        info["artist"] = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", (ex.get("Artist", {}) or {}).get("value", "")))).strip()[:80]
        info["mime"] = ii.get("mime", "")
    return info


out = []
for i, (brand, name, wiki, cat, sub, price, stock, tags, query) in enumerate(MASTER, 1):
    row = dict(n=i, brand=brand, name=name, category=cat, subcategory=sub, price=price, stock=stock, tags=tags, fallback=query, wiki=wiki)
    if wiki:
        try:
            info = lookup(wiki)
        except Exception as e:
            info = None; print("ERR", wiki, e)
        if info:
            row.update(info)
            ok_img = (info.get("orig") and info["w"] >= 700 and info["h"] >= 500 and info.get("mime") in ("image/jpeg", "image/png")
                      and any(k in info.get("license", "").lower() for k in FREE) and "non-free" not in info.get("license", "").lower())
            row["wiki_photo"] = bool(ok_img)
            if ok_img:
                try:
                    url = info["orig"] if info["w"] <= 2400 else re.sub(r"/commons/", "/commons/thumb/", info["orig"]) + f"/2000px-{info['file']}"
                    r = requests.get(url, headers=H, timeout=60)
                    if r.ok and r.headers.get("content-type", "").startswith("image"):
                        (RAW / f"{i:03d}.jpg").write_bytes(r.content)
                    else:
                        row["wiki_photo"] = False
                except Exception as e:
                    print("dl fail", wiki, e); row["wiki_photo"] = False
        else:
            print("MISSING", wiki)
    print(f"{i:3d} {brand} {name:34s} wiki={'Y' if row.get('url') else '-'} photo={'Y' if row.get('wiki_photo') else '-'} {row.get('license','')}")
    out.append(row); time.sleep(0.25)
(ROOT / ".run" / "catalog_stage1.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
print("wiki articles:", sum(1 for r in out if r.get("url")), "wiki photos:", sum(1 for r in out if r.get("wiki_photo")), "of", len(out))
