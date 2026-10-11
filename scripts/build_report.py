"""Assemble docs/Project_Documentation.docx from diagrams, screenshots, evaluation and test results.

Usage: python scripts/make_diagrams.py && python scripts/evaluate.py && python scripts/build_report.py
"""
import json
import re
import subprocess
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
D, S = ROOT / "docs" / "diagrams", ROOT / "docs" / "screenshots"
NAVY = RGBColor(0x1E, 0x3A, 0x5F)

doc = Document()
sec = doc.sections[0]
sec.left_margin = sec.right_margin = Inches(0.9)
sec.top_margin = sec.bottom_margin = Inches(0.8)
st = doc.styles["Normal"]
st.font.name, st.font.size = "Calibri", Pt(11)
for name, size in (("Heading 1", 18), ("Heading 2", 14), ("Heading 3", 12)):
    h = doc.styles[name]
    h.font.name, h.font.size, h.font.color.rgb = "Calibri", Pt(size), NAVY


def shade(cell, hex_):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hex_)
    tcPr.append(shd)


def para(text="", bold=False, italic=False, size=None, align=None, color=None, space_after=6):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    if size: r.font.size = Pt(size)
    if color: r.font.color.rgb = color
    if align == "c": p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(space_after)
    return p


def bullets(items):
    for t in items:
        doc.add_paragraph(t, style="List Bullet")


def table(headers, rows, widths=None, font=9.5):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.autofit = False
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(font); r.font.color.rgb = RGBColor(255, 255, 255)
        shade(c, "1E3A5F")
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(font)
    if not any(headers):
        t._tbl.remove(t.rows[0]._tr)
    if widths:
        for i, w in enumerate(widths):
            t.columns[i].width = Inches(w)
        for row in t.rows:
            for c, w in zip(row.cells, widths):
                c.width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def figure(path, caption, width=6.6):
    doc.add_picture(str(path), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    para(caption, italic=True, size=9.5, align="c", color=RGBColor(0x47, 0x55, 0x69), space_after=10)


# ------------------------------------------------------------------ cover
para("PIMPRI CHINCHWAD UNIVERSITY", True, size=18, align="c", color=NAVY, space_after=0)
para("Sate, Maval, Pune - 412106", align="c", space_after=0)
para("School of Computer Applications · Department of MCA", align="c", space_after=40)
para("PROJECT DOCUMENTATION", True, size=12, align="c", color=RGBColor(0x1F, 0x8A, 0x8A), space_after=10)
para("CURIO - AI-Based Product Recommendation System", True, size=26, align="c", color=NAVY, space_after=4)
para("Content-Based Product Discovery for E-Commerce", italic=True, size=14, align="c", space_after=40)
para("Submitted in partial fulfilment of the requirements for the degree of", align="c", space_after=2)
para("Master of Computer Applications (MCA)", True, size=14, align="c", space_after=30)
para("Submitted by", size=10, align="c", space_after=2)
para("Yogendra Shashikant Gawade", True, size=16, align="c", space_after=10)
table(["", ""], [["MCA Roll No.", "MCA25229"], ["SCA Roll No.", "SCA25802010016"],
                  ["Semester / Year", "3rd Semester, 2nd Year"], ["Project Domain", "Artificial Intelligence and Machine Learning"],
                  ["Technology", "Python · Streamlit · MongoDB · PyMongo · Pandas · scikit-learn"], ["Catalogue", "125 real luxury pieces from 72 maisons in 8 collections"]], [1.8, 4.4], 11)
doc.add_page_break()

# ------------------------------------------------------------------ contents
doc.add_heading("Contents of this document", 1)
bullets(["1  Project overview, scope and feature list", "2  System architecture and module hierarchy", "3  Data design: ERD, MongoDB design, data dictionary",
         "4  UML and data-flow diagrams (use case, class, sequence, state, DFD)", "5  Recommendation engines (similar items, bought together)",
         "6  Payment gateway (demo Razorpay)", "7  User interface and landing page (screenshots)", "8  Validations and error handling",
         "9  Testing and results", "10  Offline evaluation", "11  How to run, limitations and future scope"])

doc.add_heading("1  Project overview", 1)
para("CURIO is a complete luxury e-commerce prototype that combines a content-based recommendation engine with the features of a real store: accounts, catalogue search and filters, "
     "wishlist, reviews, bag, coupons, delivery options with GST, a simulated Razorpay payment gateway, order tracking with cancellation and refunds, invoices and an admin console. "
     "The catalogue holds 125 real pieces from 72 maisons in 8 collections (Watches, Bags, Jewellery, Fragrance, Eyewear, Apparel, Footwear, Leather & writing), for example the Rolex Submariner, "
     "Hermès Kelly, Chanel N°5 and the Cartier Love bracelet. 30 product descriptions are the opening text of the model's English Wikipedia article (CC BY-SA 4.0); the rest are short factual descriptions written for the demo. "
     "Prices are indicative. Photographs are professional images from Unsplash chosen per brand and model (assets/CREDITS.md); they show the piece or a very similar one, not necessarily the exact reference. "
     "The storefront follows the editorial minimalism of a fashion-house site.")
doc.add_heading("Synopsis objectives and where they are met", 2)
table(["#", "Objective (synopsis)", "Implementation"],
      [["1", "Streamlit interface for browsing, searching, filtering, product details", "ui/shop_pages.py, ui/landing.py"],
       ["2", "Cart operations and order placement", "shop/cart.py, shop/orders.py, ui/checkout.py"],
       ["3", "Store products, users, carts, orders in MongoDB", "shop/db.py; 8 collections (section 3)"],
       ["4", "Recommendation engine: attributes, TF-IDF, cosine similarity", "shop/recommender.py"],
       ["5", "Show similar products in the exploration workflow", "Product page: You may also like"],
       ["6", "Demonstrate and test the integrated system", "156+ automated tests; real-browser end-to-end run; screenshots"]], [0.3, 3.3, 2.9])
doc.add_heading("Extensions beyond the synopsis", 2)
bullets(["Frequently bought together: market-basket confidence and lift over past orders, with Add all to bag.",
         "Demo payment gateway modelled on Razorpay test mode (UPI, card with bank page, netbanking, COD) with HMAC signature verification, failure paths and refunds.",
         "Accounts with scrypt-hashed passwords and customer / admin roles; address book; wishlist; verified-buyer reviews.",
         "Coupons, delivery methods with PIN-code estimates, GST breakdown, downloadable invoice, order timeline, cancellation, auto-expiry of unpaid orders.",
         "Admin console: KPI dashboard, order fulfilment, product and photo management, coupons.",
         "Editorial minimalist storefront (pinned wordmark, scroll-unfolding campaign slides, tile wall) with CSS-only motion, no emoji, fully responsive; one-command start and stop scripts with prerequisite checks."])
doc.add_heading("Scope boundary", 2)
bullets(["Payments are simulated; no real money moves, nothing is shipped, taxes and refunds are illustrative.",
         "Recommendations are item-to-item (content and co-purchase), not personalised per user; deep learning is out of scope.",
         "Co-purchase statistics start from synthetic seeded history that is flagged and disclosed; real orders add to it."])

# ------------------------------------------------------------------ 2 architecture
doc.add_heading("2  System architecture and module hierarchy", 1)
figure(D / "02_architecture.png", "Figure 2.1 - Layered system architecture", 6.4)
figure(D / "03_module_hierarchy.png", "Figure 2.2 - Module hierarchy", 6.8)

# ------------------------------------------------------------------ 3 data design
doc.add_heading("3  Data design", 1)
figure(D / "01_erd.png", "Figure 3.1 - Entity Relationship Diagram", 6.6)
para("Nine MongoDB collections: users, addresses, products, carts, wishlists, reviews, coupons, orders, payments (plus a meta document with the schema version). Cart lines, order lines, "
     "the order timeline and wishlist ids are embedded arrays. Order lines and the delivery address are snapshots so history never changes. Card numbers and CVV are never stored.")
dd = {
    "users": [["_id", "string", "U- + 8 hex", "Identifier"], ["name", "string", "2-60 chars", "Display name"], ["email", "string", "unique, lower-case", "Login"],
              ["password_hash", "string", "scrypt, salted", "Never shown"], ["role", "string", "customer | admin", "Access level"], ["created_at", "datetime", "UTC", "Registered"]],
    "products": [["_id", "string", "P001..", "Identifier"], ["name / brand", "string", "2-120 / 1-60", "Name, brand"], ["category / subcategory", "string", "8 / 31 values", "Taxonomy"],
                 ["price", "double", "> 0, GST inclusive", "INR"], ["stock", "int", "0-100000", "Units"], ["image", "string", "assets path or URL", "Photo"],
                 ["tags / description", "array / text", "<=20 tags / 10-1000 chars", "Recommender input"]],
    "orders": [["_id", "string", "ORD-YYYYMMDD-XXXXXX", "Order number"], ["items[]", "array", "snapshot lines", "Purchased lines"], ["pricing", "object", "subtotal, discount, shipping, GST, total", "Price breakdown"],
               ["address", "object", "snapshot", "Delivery address"], ["payment", "object", "method, status, ids, last4", "Payment state"],
               ["status", "string", "Pending Payment..Delivered, Cancelled", "Lifecycle"], ["timeline[]", "array", "status, time, note", "Tracking"]],
    "payments": [["_id", "string", "order_...", "Gateway order id"], ["amount", "int", "paise", "Amount"], ["status", "string", "created..captured/refunded", "State"],
                 ["payment_id / signature", "string", "pay_..., HMAC-SHA256", "Verification"]],
    "other": [["addresses", "", "phone 10 digits, PIN 6 digits, one default per user", "Address book"], ["wishlists", "", "product_ids[] per user", "Saved items"],
              ["reviews", "", "rating 1-5, one per user per product, verified flag", "Reviews"], ["coupons", "", "percent/flat, min order, categories, cap, expiry, limit", "Discounts"]],
}
for coll, rows in dd.items():
    doc.add_heading(f"Collection(s): {coll}", 3)
    table(["Field", "Type", "Constraint / rule", "Description"], rows, [1.7, 1.0, 2.4, 1.4], 9)
para("Full dictionary, indexes, integrity rules and sample documents: docs/DATABASE_DESIGN.md.", italic=True)

# ------------------------------------------------------------------ 4 UML / DFD
doc.add_heading("4  UML and data-flow diagrams", 1)
figure(D / "05_use_case.png", "Figure 4.1 - Use case diagram", 6.8)
figure(D / "07_class_services.png", "Figure 4.2 - Class diagram: application services", 6.9)
figure(D / "08_sequence_recommend.png", "Figure 4.3 - Sequence diagram: view product and similar items", 6.3)
figure(D / "09_sequence_payment.png", "Figure 4.4 - Sequence diagram: online payment", 6.0)
figure(D / "10_order_lifecycle.png", "Figure 4.5 - Order lifecycle (state diagram)", 6.8)
figure(D / "12_dfd_level0.png", "Figure 4.6 - DFD level 0", 6.4)
figure(D / "13_dfd_level1.png", "Figure 4.7 - DFD level 1", 6.8)

# ------------------------------------------------------------------ 5 recommender
doc.add_heading("5  Recommendation engine", 1)
figure(D / "11_flow_recommendation.png", "Figure 5.1 — Recommendation pipeline", 6.9)
bullets(["Text per product = name + category + brand + tags (×2) + description.",
         "TfidfVectorizer(stop_words='english', sublinear_tf=True) builds a sparse matrix; rows are L2-normalised so cosine similarity = dot product.",
         "Only the selected product's row is multiplied with the matrix (no dense all-pairs similarity matrix).",
         "Eligibility filter: excludes the product itself, same-name duplicates and out-of-stock items; N is configurable (3–8 in the UI).",
         "If nothing is similar: a clearly labelled same-category fallback (no invented score) or an informative empty state.",
         "Explainability: each result lists shared tags / same category / same brand; the UI states that similarity is not a purchase probability.",
         "The model is rebuilt only when catalogue text changes (content fingerprint); stock and price changes apply immediately."])
doc.add_heading("Frequently bought together", 2)
para("For a product p and another product q over placed orders: confidence(p to q) = orders containing both / orders containing p, and lift = confidence / share of all orders containing q. "
     "Candidates need at least 2 co-occurring orders and lift above 1; ranking is confidence x lift. The product page shows the top three with 'In X% of orders with this item' and an Add all to bag action. "
     "Starting history is ~850 synthetic orders generated from shopping missions (watch collector, executive upgrade, the gift, evening, wardrobe edit, tailoring, travel, ...) and flagged synthetic; real orders are added to the same pool and the analysis refreshes when orders change.")

doc.add_heading("6  Payment gateway (demo Razorpay)", 1)
para("The gateway reproduces the shape of Razorpay Standard Checkout in test mode. No real money moves and nothing is charged.")
bullets(["Server creates a gateway order (amount in paise) for a Pending Payment order; stock is reserved meanwhile.",
         "Checkout dialog offers UPI (success@razorpay pays, failure@razorpay fails), cards (Razorpay test cards, Luhn-validated, with a test bank page to choose Success or Failure) and netbanking.",
         "On success the gateway returns payment_id and signature = HMAC-SHA256(order_id|payment_id, secret). The server verifies the signature and that the amount equals the order total before marking the order paid; tampered signatures, wrong orders and amount mismatches are rejected (tested).",
         "Failures keep the order Pending Payment and allow retry; unpaid orders expire after 15 minutes and release stock; cancelling a paid order restocks and refunds.",
         "Only network and last four digits are stored. Going live means implementing the same PaymentGateway methods with the razorpay SDK and Checkout.js."])
figure(S / "17_razorpay_demo_dialog.png", "Figure 6.1 - Secure checkout dialog (demo Razorpay)", 5.8)
figure(S / "21_bank_page.png", "Figure 6.2 - Test bank authentication step", 5.8)



# ------------------------------------------------------------------ 6 UI
doc.add_heading("7  User interface and landing page", 1)
para("Design direction: editorial minimalism in the manner of a fashion-house site. Black on white, tiny uppercase grotesque type (Inter) with a Didone face (Bodoni Moda) for the wordmark and titles, "
     "warm-grey 3:4 image tiles, no borders, shadows, badges or rounded corners, outlined buttons and a numbered category index ([01] View all, [02] Watches ...). "
     "The landing page is a sequence of full-bleed campaign slides under a giant wordmark that stays pinned and inverts over the imagery; each slide unfolds from a framed crop as it scrolls into view "
     "(CSS scroll-driven animation) and an edge-to-edge wall of product images follows. The product page pairs a large portrait image with a pinned details column. "
     "All motion is CSS only and is disabled for users who prefer reduced motion. There are no emoji; icons are thin SVG or Material icons. The grid adapts from 2 columns on phones to 5 on wide screens.")
shots = [("01_landing_hero.png", "Landing: full-bleed campaign slide with the pinned wordmark"), ("02_landing_wall.png", "Landing: edge-to-edge product wall"),
         ("03_landing_watch.png", "Landing: The Watch Edit slide (unfolds on scroll)"), ("04_landing_bags_jewellery.png", "Landing: paired bag and jewellery slides"),
         ("05_landing_fragrance.png", "Landing: fragrance slide"), ("06_landing_new_arrivals.png", "Landing: new arrivals tiles"), ("07_landing_atelier.png", "Landing: atelier slide and service notes"),
         ("08_collection.png", "Collection page with numbered index"), ("09_watches_index.png", "Watches with subcategory index"), ("10_filters.png", "Maison and price filters"),
         ("11_product_page.png", "Product page: large image, pinned details"), ("12_frequently_bought_together.png", "Frequently bought together"),
         ("13_similar_and_reviews.png", "Similar pieces with reasons, and reviews"), ("14_log_in_error.png", "Log-in validation"), ("15_bag_with_coupon.png", "Bag with coupon applied"),
         ("16_checkout.png", "Checkout: address, delivery, payment"), ("18_payment_failed.png", "Failed payment keeps the order pending"), ("19_order_confirmation.png", "Order confirmation"),
         ("20_order_tracking.png", "Order tracking"), ("22_my_orders.png", "Account: orders"), ("23_order_cancelled.png", "Cancelled order (stock restored, refund)"),
         ("24_admin_dashboard.png", "Admin dashboard"), ("25_admin_orders.png", "Admin: order fulfilment"), ("26_admin_products.png", "Admin: products"), ("27_admin_coupons.png", "Admin: coupons"),
         ("28_mobile_landing.png", "Phone (390 px): landing"), ("29_mobile_collection.png", "Phone: collection"), ("28_tablet_landing.png", "Tablet (820 px): landing"),
         ("29_tablet_collection.png", "Tablet: collection"), ("29_wide_collection.png", "Wide (1920 px): five-column collection")]
for i, (f, c) in enumerate(shots, 1):
    if (S / f).exists():
        figure(S / f, f"Figure 6.{i} — {c}", 4.2 if f.startswith(("14", "15")) else 6.0)

# ------------------------------------------------------------------ 7 validation
doc.add_heading("8  Validations and error handling", 1)
table(["Area", "Rule", "Where"],
      [["Accounts", "Name 2-60 letters; valid unique email; password 8-128 chars with a letter and a digit; scrypt hash; generic 'incorrect email or password' (no account enumeration, equal timing)", "validators.py, users.py"],
       ["Addresses", "10-digit Indian mobile (6-9...), 6-digit PIN, line 1 5-120, city, state; private to the owner", "validators.py, addresses.py"],
       ["Search / filters", "Trimmed, <=100 chars, regex-escaped; brand and price filters", "validators.py, catalog.py"],
       ["Bag", "Whole-number quantity 1-10 not above stock; out-of-stock cannot be added; deleted or over-stock lines block checkout", "cart.py"],
       ["Coupons", "Exists, active, not expired, under usage limit, minimum order met, category restriction, discount cap", "coupons.py"],
       ["Checkout", "Non-empty bag, owned address, stock re-checked and reserved atomically with rollback, COD limit 50,000", "orders.py"],
       ["Payment", "Luhn card, expiry in future, CVV, UPI format; test-value gate; signature and amount verified server-side; card data not stored", "validators.py, payments.py"],
       ["Order actions", "Only the owner can pay or cancel; cancel only before shipping; status moves one step at a time and only by an admin", "orders.py"],
       ["Reviews", "Rating 1-5, title 2-80, body 10-1500, one per user per product", "validators.py, reviews.py"],
       ["Admin", "Role checked in the UI and again in the service layer; product form rules; photo upload type, size and dimension checks", "orders.py, media.py, validators.py"],
       ["Failures", "Database errors become friendly messages; unexpected errors never show stack traces", "ui/state.py"],
       ["Secrets", "Settings from environment / .env, never in source", "config.py"]], [1.1, 4.0, 1.4])

# ------------------------------------------------------------------ 8 testing
doc.add_heading("9  Testing and results", 1)
res = subprocess.run([sys.executable, "-m", "pytest", "--co", "-q"], cwd=ROOT, capture_output=True, text=True).stdout
counts = {}
for line in res.splitlines():
    m = re.match(r"tests/(\w+)\.py::", line)
    if m:
        counts[m.group(1)] = counts.get(m.group(1), 0) + 1
run = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT, capture_output=True, text=True).stdout.strip().splitlines()
summary = run[-1] if run else "n/a"
cover = {"test_validators": "Input validation rules", "test_catalog": "Search, filters, sorts, best sellers, product management",
         "test_cart_orders": "Bag, checkout, COD, online payment, failed and tampered payments, cancel / refund / expiry, admin status flow",
         "test_accounts": "Password hashing, sign-in, roles, addresses, wishlist, reviews, coupons",
         "test_bundles_stats": "Bought-together statistics, pricing, invoice, dashboard",
         "test_recommender": "Similarity ranking, eligibility filter, fallback, caching, explainability, speed",
         "test_media": "Photo resolution, upload validation, path safety",
         "test_app_ui": "Headless UI journeys: landing, no emoji, collection index, sign-in, register, bundle, checkout, admin gate"}
table(["Test module", "Tests", "Covers"], [[k, v, cover.get(k, "")] for k, v in counts.items()] + [["TOTAL", sum(counts.values()), ""]], [1.6, 0.7, 4.2])
para(f"Result of the final run: {summary}", True)
doc.add_heading("Synopsis test scenarios (section 10)", 2)
table(["Scenario", "Expected result", "Automated test", "Status"],
      [["Search and filter products", "Relevant products shown", "test_catalog, test_app_ui::test_catalog_search_*", "Pass"],
       ["Open a product", "Details, bought together, similar items", "test_app_ui::test_product_page_has_*", "Pass"],
       ["Add / remove / update bag", "Bag reflects the operation", "test_cart_orders::test_add_and_total, test_update_and_remove", "Pass"],
       ["Place an order (COD, online)", "Items, totals, GST stored; stock reserved", "test_cod_order_end_to_end, test_online_payment_happy_path", "Pass"],
       ["Payment failure / tampering", "Order stays pending; verification rejects", "test_failed_payments_*, test_tampered_signature_*", "Pass"],
       ["Cancel, refund, expiry", "Stock restored, refund recorded", "test_cancel_paid_order_*, test_pending_orders_expire_*", "Pass"],
       ["Stock changed by someone else", "Order refused, nothing reserved", "test_stock_rechecked_and_rolled_back", "Pass"],
       ["Invalid input / security", "Friendly messages; role checks", "test_validators, test_accounts, test_status_flow_and_admin_only", "Pass"]], [1.5, 1.7, 2.6, 0.6], 9)
para("Tests run on mongomock by default; the service and UI suites also pass against a real MongoDB 7 container. scripts/make_screenshots.py additionally drives the real app in Chrome through UPI payment, a failed payment, card with the bank page, cash on delivery, cancellation and the admin console, and fails if any step misbehaves.", italic=True)

# ------------------------------------------------------------------ 9 evaluation
doc.add_heading("10  Offline evaluation", 1)
ev = json.loads((ROOT / "docs" / "evaluation_results.json").read_text())
e = ev["environment"]
para(f"Catalogue {e['catalog_size']} products · {e['queries']} queries (every in-stock product) · K = {e['K']} · seed {e['seed']} · "
     f"scikit-learn {e['scikit-learn']} · Python {e['python']}.")
para("Relevance proxy: a candidate is relevant when it has the same subcategory label as the query product. The label is not a model feature. "
     "This is a conservative stand-in for the independent human judgments proposed in the synopsis; it makes no claim about sales or user satisfaction.", italic=True)
cols = ["P@3", f"P@{e['K']}", "MRR", "Coverage", "Empty lists"]
table(["Method"] + cols, [[m] + [f"{r[c]:.3f}" for c in cols] for m, r in ev["results"].items()], [2.2, 0.8, 0.8, 0.8, 0.9, 1.0])
r = ev["responsiveness"]
table(["Responsiveness (this machine, mongomock)", "ms"],
      [["Feature rebuild (TF-IDF fit), mean", f"{r['feature_build_ms_mean']:.2f}"],
       ["Similarity + ranking only, median / p95", f"{r['model_only_ms_median']:.3f} / {r['model_only_ms_p95']:.3f}"],
       ["End-to-end (fetch catalogue + rank), median / p95", f"{r['end_to_end_ms_median']:.2f} / {r['end_to_end_ms_p95']:.2f}"]], [4.5, 2.0])
para("Interpretation: TF-IDF clearly outperforms the random and category-only baselines. Subcategories contain only a few products, which caps attainable precision, and cross-subcategory suggestions "
     "(a wallet for a watch) count as non-relevant under this conservative proxy. Apparel scores lowest because many garment descriptions share generic wording; this is reported rather than tuned away. Results on a real catalogue would differ.")
# ------------------------------------------------------------------ 10 run / limits
doc.add_heading("11  How to run, limitations and future scope", 1)
para("Run:  ./start.sh  (checks Python, packages, ports, Docker and MongoDB health, starts MongoDB 7 via docker compose, seeds data, serves http://localhost:8501).  Stop:  ./stop.sh  (--purge deletes data).  "
     "Demo logins: demo@example.com / Demo@1234 (customer), admin@curio.test / Admin@1234 (admin). Test payments: UPI success@razorpay, card 4111 1111 1111 1111.", True)
doc.add_heading("Limitations", 2)
bullets(["The payment gateway is a simulation modelled on Razorpay test mode; no real money moves. Delivery, tax and refunds are simulated.",
         "Photographs are Unsplash images selected per brand and model; they may show a similar piece rather than the exact reference. Brand names are trademarks of their owners and are used for illustration; prices are indicative.",
         "Bought-together statistics start from synthetic seeded orders (flagged and disclosed); similar-items evaluation uses a proxy relevance label.",
         "Single-store prototype: sessions in Streamlit session state, no email or SMS, no multi-document transactions (stock reservation is conditional-atomic per product with rollback)."])
doc.add_heading("Future scope", 2)
bullets(["Real Razorpay integration (SDK, Checkout.js, webhooks), shipping partner APIs, email and SMS notifications",
         "Personalised and hybrid recommendation from browsing and purchase history; natural-language search; review sentiment",
         "Cloud deployment, managed MongoDB, observability, A/B testing of recommendations"])

out = ROOT / "docs" / "Project_Documentation.docx"
doc.save(out)
print("saved", out)
