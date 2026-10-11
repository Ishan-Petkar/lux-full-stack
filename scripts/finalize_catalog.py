"""Stage 3: combine the master list, real Wikipedia text and descriptions into shop/catalog_data.json (ids P001...).
Usage: python scripts/finalize_catalog.py"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog_master import MASTER  # noqa: E402
from catalog_text import DESC, USE_WIKI  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
stage = {(r["brand"], r["name"]): r for r in json.loads((ROOT / ".run" / "catalog_stage1.json").read_text())}
out, missing = [], []
for i, (brand, name, wiki, cat, sub, price, stock, tags, fb) in enumerate(MASTER, 1):
    key = f"{brand} {name}"
    st = stage.get((brand, name), {})
    if key in USE_WIKI and st.get("extract"):
        desc, src = st["extract"], f"Wikipedia: {st['wiki']} (CC BY-SA 4.0)"
    elif key in DESC and DESC[key]:
        desc, src = DESC[key], "Written for this demo"
    elif st.get("extract"):
        desc, src = st["extract"], f"Wikipedia: {st['wiki']} (CC BY-SA 4.0)"
    else:
        missing.append(key); desc, src = f"{name} by {brand}.", ""
    if len(desc) < 10:
        desc = f"{desc} {brand}."
    out.append({"id": f"P{i:03d}", "brand": brand, "name": name, "category": cat, "subcategory": sub, "price": price, "stock": stock,
                "tags": sorted({t.strip().lower() for t in tags.split(",")}), "description": desc, "source": src})
(ROOT / "shop" / "catalog_data.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(len(out), "products;", "missing descriptions:", missing)
