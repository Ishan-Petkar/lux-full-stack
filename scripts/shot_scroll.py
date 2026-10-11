"""Dev helper: screenshot a page at successive scroll positions.  python scripts/shot_scroll.py prefix [width] [height] [steps] [url]"""
import sys
from playwright.sync_api import sync_playwright
pre = sys.argv[1]; w = int(sys.argv[2]) if len(sys.argv) > 2 else 1440; h = int(sys.argv[3]) if len(sys.argv) > 3 else 900
steps = int(sys.argv[4]) if len(sys.argv) > 4 else 6; url = sys.argv[5] if len(sys.argv) > 5 else "http://localhost:8502"
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", headless=True); p = b.new_page(viewport={"width": w, "height": h})
    p.goto(url); p.wait_for_timeout(6000)
    for i in range(steps):
        p.screenshot(path=f"{pre}_{i}.png")
        p.evaluate(f"(()=>{{const m=document.querySelector('[data-testid=\"stMain\"]'); m.scrollBy(0,{int(h*0.9)});}})()"); p.wait_for_timeout(1400)
    print("scrollHeight", p.evaluate("document.querySelector('[data-testid=\"stMain\"]').scrollHeight")); b.close()
