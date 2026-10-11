"""Explanatory diagrams for the beginner's guide: tech stack, Streamlit rerun loop, site map, TF-IDF example, basket analysis,
payment signature, start/stop script flow, scroll animation, security layers."""
from diagram_lib import *
from matplotlib.patches import Rectangle


def tech_stack(out):
    fig, ax = canvas(190, 130, "The Technology Stack, Layer by Layer", "What each tool is, and the job it does in this project")
    layers = [
        ("You (the browser)", "ui", "Chrome, Safari, Edge, phone", "Shows pages, sends your clicks", 112),
        ("Streamlit (Python)", "ui", "app.py + ui/*.py", "Turns Python into a web page; re-runs the script on every click", 92),
        ("Business logic (Python)", "proc", "shop/*.py", "The rules: stock, coupons, payments, orders, validation", 72),
        ("AI engines", "proc", "scikit-learn, NumPy, Pandas", "TF-IDF similarity and basket analysis", 52),
        ("Database driver", "data", "PyMongo", "Python's way to talk to MongoDB", 32),
        ("MongoDB 7 in Docker", "data", "docker-compose.yml", "Stores users, products, orders, payments", 12),
    ]
    for name, kind, tool, job, y in layers:
        box(ax, 8, y, 40, 14, name, kind, 9, True, r=1.2)
        box(ax, 52, y, 40, 14, tool, "neutral", 8.4, False, r=1.2)
        ax.text(97, y + 7, job, va="center", fontsize=8.4, color=INK)
        if y > 12:
            line(ax, [(28, y), (28, y - 6)], style="<|-|>", lw=1.2, ms=8)
    ax.text(95, 3, "Everything above the database runs in one Python process. Docker only packages MongoDB so you do not install it by hand.", ha="center", fontsize=8, color="#475569")
    save(fig, out)


def rerun_loop(out):
    fig, ax = canvas(190, 100, "How a Streamlit App Works (the 'rerun' idea)", "Unlike a normal website, the whole Python script runs again from the top after every click")
    steps = [("1  You click\n'Add to bag'", "ui", 6), ("2  Browser tells\nthe server\nwhich widget", "ui", 42), ("3  Server runs the\ncallback, then\napp.py from the top", "proc", 78),
             ("4  Script reads\nsession_state\n(your memory)", "proc", 114), ("5  Page is drawn\nand sent back", "ui", 150)]
    for t, k, x in steps:
        box(ax, x, 50, 34, 24, t, k, 8.4, True, r=1.5)
    for i in range(4):
        line(ax, [(steps[i][2] + 34, 62), (steps[i + 1][2], 62)], lw=1.6, ms=11)
    line(ax, [(167, 50), (167, 38), (23, 38), (23, 50)], lw=1.2, ls="--", color="#b06a14", style="-|>")
    ax.text(95, 41, "next click starts the loop again", ha="center", fontsize=8, color="#b06a14")
    box(ax, 30, 6, 130, 22, "st.session_state is a dictionary kept per browser tab. It is how the app remembers who is logged in,\nwhich product is open and the current page, even though the script restarts every time.", "dec", 8.2, r=1.2)
    save(fig, out)


def sitemap(out):
    fig, ax = canvas(200, 118, "Site Map: Every Page and How You Reach It", "Each box is a function in ui/; the arrows are buttons or links")
    box(ax, 80, 98, 40, 9, "Home (landing)", "ui", 9, True, r=1.5)
    pages = [("Collection\n(catalogue)", 8, 74, "ui"), ("Product page", 8, 48, "ui"), ("Log in /\nCreate account", 58, 74, "ui"), ("Account:\norders, wishlist,\naddresses, profile", 58, 46, "ui"),
             ("Bag", 108, 74, "flow"), ("Checkout", 108, 52, "flow"), ("Payment dialog\n(demo Razorpay)", 108, 28, "flow"), ("Confirmation", 108, 6, "flow"),
             ("Order detail\n(tracking, invoice)", 156, 8, "flow"), ("Admin console:\ndashboard, orders,\nproducts, coupons", 156, 74, "data"), ("Help centre", 156, 50, "ui")]
    for t, x, y, k in pages:
        box(ax, x, y, 36, 16, t, k, 7.8, True, r=1.2)
    d = dict(lw=1.1, ms=9)
    line(ax, [(100, 98), (26, 90)], **d)
    line(ax, [(100, 98), (76, 90)], **d)
    line(ax, [(26, 74), (26, 64)], **d)
    line(ax, [(44, 56), (108, 80)], ls="--", **d)
    line(ax, [(126, 74), (126, 68)], **d)
    line(ax, [(126, 52), (126, 44)], **d)
    line(ax, [(126, 28), (126, 22)], **d)
    line(ax, [(144, 14), (156, 15)], **d)
    line(ax, [(76, 74), (76, 62)], **d)
    line(ax, [(120, 98), (156, 90)], ls="--", **d)
    ax.text(100, 2, "Dashed = optional or admin only.  Every page is wrapped by the fixed header and the footer.", ha="center", fontsize=7.8, color="#475569")
    save(fig, out)


def tfidf_example(out):
    fig, ax = canvas(200, 118, "TF-IDF + Cosine Similarity: a Worked Example", "Three tiny 'products' described in a few words, so you can follow the maths")
    ax.text(100, 106, "Step 1 - look at each description", ha="center", fontsize=9.5, fontweight="bold", color=INK)
    docs = [("A  Sports watch", "steel diver watch"), ("B  Dress watch", "gold dress watch"), ("C  Perfume", "citrus fresh perfume")]
    for i, (n, t) in enumerate(docs):
        box(ax, 8 + i * 62, 86, 56, 14, f"{n}\n\"{t}\"", ["ui", "ui", "data"][i], 8.4, True, r=1)
    ax.text(100, 78, "Step 2 - count words, then down-weight words that appear everywhere (the 'IDF' part)", ha="center", fontsize=9.5, fontweight="bold", color=INK)
    hdr = ["", "steel", "diver", "watch", "gold", "dress", "citrus", "fresh", "perfume"]
    vals = [["A", "0.50", "0.50", "0.38", "0", "0", "0", "0", "0"], ["B", "0", "0", "0.38", "0.50", "0.50", "0", "0", "0"], ["C", "0", "0", "0", "0", "0", "0.50", "0.50", "0.50"]]
    cw, x0, y0 = 20, 18, 60
    for j, h in enumerate(hdr):
        ax.add_patch(Rectangle((x0 + j * cw - 8, y0), cw, 6, fc="#1e3a5f", ec="white"))
        ax.text(x0 + j * cw + 2, y0 + 3, h, ha="center", va="center", color="white", fontsize=7.6, fontweight="bold")
    for i, row in enumerate(vals):
        for j, v in enumerate(row):
            hi = j > 0 and v != "0"
            ax.add_patch(Rectangle((x0 + j * cw - 8, y0 - 6 * (i + 1)), cw, 6, fc="#e6dff0" if hi else "#f8fafc", ec="#cbd5e1"))
            ax.text(x0 + j * cw + 2, y0 - 6 * (i + 1) + 3, v, ha="center", va="center", fontsize=7.8, fontweight="bold" if j == 0 else "normal")
    ax.text(100, 34, "Step 3 - compare two rows with cosine similarity (how much the two lists of numbers point the same way)", ha="center", fontsize=9.5, fontweight="bold", color=INK)
    box(ax, 10, 12, 56, 16, "A vs B\nshare 'watch' only\nsimilarity = 0.38 x 0.38 = 0.14", "flow", 8.2, True, r=1)
    box(ax, 72, 12, 56, 16, "A vs C\nshare nothing\nsimilarity = 0.00", "red", 8.2, True, r=1)
    box(ax, 134, 12, 56, 16, "Ranking for A:\n1. B (0.14)\n2. C (0.00, not shown)", "dec", 8.2, True, r=1)
    ax.text(100, 4, "1 = identical wording, 0 = nothing in common. The real catalogue works the same way with many hundreds of distinct words.", ha="center", fontsize=8, color="#475569")
    save(fig, out)


def basket(out):
    fig, ax = canvas(200, 98, "'Frequently Bought Together': the Maths in Plain Numbers", "Worked example with 100 past orders")
    box(ax, 6, 56, 54, 30, "100 orders in total\n40 contain the watch (W)\n30 contain the wallet (L)\n18 contain BOTH", "ui", 9, True, r=1.5)
    box(ax, 70, 56, 60, 30, "Confidence(W to L)\n= 18 / 40 = 45%\n'45% of people who bought\nthe watch also bought the wallet'", "flow", 9, True, r=1.5)
    box(ax, 140, 56, 54, 30, "Lift\n= 45% / (30/100 = 30%) = 1.5\n1.5 > 1, so they go together more\nthan chance would explain", "proc", 8.6, True, r=1.5)
    line(ax, [(60, 71), (70, 71)], lw=1.6, ms=11)
    line(ax, [(130, 71), (140, 71)], lw=1.6, ms=11)
    box(ax, 15, 24, 170, 20, "Ranking score = confidence x lift = 0.45 x 1.5 = 0.68.  A pair must appear in at least 2 orders (minimum support)\nand have lift above 1 to be shown. The top 3 become 'Frequently bought together'.", "dec", 8.4, r=1.2)
    ax.text(100, 10, "Lift near 1 means two popular items that just happen to share many baskets; lift above 1 means a real link.", ha="center", fontsize=8.4, color="#475569")
    save(fig, out)


def signature(out):
    fig, ax = canvas(200, 108, "How the Payment Signature Stops Cheating", "The server never trusts the browser; it re-computes a secret fingerprint (HMAC-SHA256)")
    box(ax, 4, 60, 40, 30, "Payment dialog\n(browser)\nreceives payment_id\n+ signature", "ui", 8.4, True, r=1.5)
    box(ax, 80, 60, 50, 30, "Server holds the secret key\n(never sent to the browser)\nexpected =\nHMAC(order_id | payment_id)", "proc", 8.2, True, r=1.5)
    box(ax, 158, 60, 40, 30, "Compare\nsignature == expected\nand amount == total?", "dec", 8.2, True, r=1.5)
    line(ax, [(44, 75), (80, 75)], lw=1.6, ms=11, label="ids + signature", ldy=3.5, lfs=7.4)
    line(ax, [(130, 75), (158, 75)], lw=1.6, ms=11)
    box(ax, 120, 24, 74, 20, "Match: order becomes 'Placed', stock kept,\ncoupon redeemed.", "flow", 8.4, True, r=1.2)
    box(ax, 6, 24, 100, 20, "No match (someone edited the browser data):\npayment rejected, order stays 'Pending Payment'.", "red", 8.4, True, r=1.2)
    line(ax, [(180, 60), (180, 44)], lw=1.2, ms=9, label="yes", lcolor="#2f7d4f", ldx=4, ldy=0)
    line(ax, [(165, 60), (96, 44)], lw=1.2, ms=9, color="#b42318", label="no", lcolor="#b42318", lpos=(135, 53))
    ax.text(100, 10, "Without the secret key nobody can forge a valid signature, which is why the check runs on the server.", ha="center", fontsize=8.4, color="#475569")
    save(fig, out)


def start_flow(out):
    fig, ax = canvas(190, 128, "What ./start.sh Does", "Every step is a check; any failure prints the exact fix and stops (exit code 1)")
    steps = ["Project files present?", "Already running? (then stop here)", "Python 3.10+ installed?", "Virtual env + packages (create / install)", "Ports 8501 and 27017 free?",
             "Docker CLI, compose, daemon (start colima if down)", "MongoDB container healthy?", "Connect from Python, seed 125 products", "Start Streamlit, wait for /_stcore/health"]
    for i, t in enumerate(steps):
        y = 108 - i * 11.4
        box(ax, 20, y - 4, 100, 8.4, f"{i + 1}.  {t}", "flow" if i != 1 else "dec", 8.2, False, r=1, align="left")
        if i < len(steps) - 1:
            line(ax, [(70, y - 4), (70, y - 7)], lw=1.2, ms=8)
        if i != 1:
            line(ax, [(120, y), (134, y)], lw=1.0, color="#b42318", ms=8)
    box(ax, 134, 40, 52, 44, "If a check fails:\nprint what is wrong\nand how to fix it,\nthen exit 1.\n\nNothing half-started\nis left running.", "red", 8.4, True, r=1.2)
    box(ax, 20, 2, 100, 8, "Running at http://localhost:8501   (stop with ./stop.sh)", "term", 8.6, True, r=2)
    save(fig, out)


def scroll_anim(out):
    fig, ax = canvas(200, 90, "How the Scroll 'Unfold' Animation Works (CSS only, no JavaScript)", "The browser ties the animation's progress to how far the element has scrolled into view")
    for i, (x, t, inset) in enumerate([(8, "Slide just entering", 16), (74, "Half-way in", 8), (140, "Fully in view", 0)]):
        ax.add_patch(Rectangle((x, 30), 52, 40, fc="#f1f5f9", ec="#475569", lw=1.2))
        ax.add_patch(Rectangle((x + inset * .6, 30 + inset * .5), 52 - inset * 1.2, 40 - inset, fc="#2f7d4f" if i == 2 else "#8aa", ec="none", alpha=.85))
        ax.text(x + 26, 24, t, ha="center", fontsize=8.6, fontweight="bold")
    line(ax, [(60, 50), (74, 50)], lw=1.5, ms=10)
    line(ax, [(126, 50), (140, 50)], lw=1.5, ms=10)
    box(ax, 6, 4, 188, 12, "animation-timeline: view();   @keyframes unfold { from { clip-path: inset(16% 14%); transform: scale(1.22) }  to { clip-path: inset(0); transform: scale(1) } }", "neutral", 7.2, r=1)
    ax.text(100, 78, "As you scroll, the picture grows from a framed crop to full-bleed. Browsers without support simply show the full image.", ha="center", fontsize=8.4, color="#475569")
    save(fig, out)


def security_layers(out):
    fig, ax = canvas(190, 112, "Security Layers (what protects what)", "Defence in depth: each layer assumes the one before it can fail")
    rows = [("Input validation", "validators.py: names, emails, phone, PIN, card (Luhn), UPI, quantities, search text", "ui", 94),
            ("Authentication", "scrypt-hashed passwords with random salt; identical error for wrong email or wrong password", "proc", 76),
            ("Authorisation", "role check in the UI and again inside the service (require_admin); users only touch their own orders", "proc", 58),
            ("Payment integrity", "HMAC signature + amount checked on the server; card number and CVV never stored", "flow", 40),
            ("Data integrity", "conditional stock updates, roll-back, unique indexes, snapshots of price and address", "data", 22),
            ("Secrets", "settings from environment / .env, never in source; .env is git-ignored", "dec", 4)]
    for n, d, k, y in rows:
        box(ax, 6, y, 44, 14, n, k, 9, True, r=1)
        ax.text(54, y + 7, d, va="center", fontsize=8.2, color=INK)
    save(fig, out)


def run(OUT):
    tech_stack(OUT / "14_tech_stack.png")
    rerun_loop(OUT / "15_streamlit_rerun.png")
    sitemap(OUT / "16_site_map.png")
    tfidf_example(OUT / "17_tfidf_example.png")
    basket(OUT / "18_basket_maths.png")
    signature(OUT / "19_payment_signature.png")
    start_flow(OUT / "20_start_script_flow.png")
    scroll_anim(OUT / "21_scroll_animation.png")
    security_layers(OUT / "22_security_layers.png")
