"""Diagrams for the expanded system: ERD, architecture, module hierarchy, use case, class (services),
payment sequence, order lifecycle, DFD level 1."""
from matplotlib.patches import Rectangle
from diagram_lib import *
import diagrams_b as B


def erd(out):
    fig, ax = canvas(215, 150, "Entity Relationship Diagram", "Logical view. MongoDB embeds CartItem / OrderItem / Timeline as arrays inside Cart and Order documents.")
    U = table(ax, 86, 140, 44, "USER", [("user_id", "string", "PK"), ("name", "string", ""), ("email", "unique", ""), ("password_hash", "scrypt", ""), ("role", "customer|admin", ""), ("created_at", "datetime", "")], "ui")
    A = table(ax, 8, 140, 44, "ADDRESS", [("address_id", "string", "PK"), ("user_id", "string", "FK"), ("label / name", "string", ""), ("phone", "10 digits", ""), ("line1 / line2", "string", ""), ("city / state", "string", ""), ("pincode", "6 digits", ""), ("is_default", "bool", "")], "ui")
    W = table(ax, 164, 140, 44, "WISHLIST", [("user_id", "string", "PK,FK"), ("product_ids[]", "string[]", "")], "ui")
    R = table(ax, 164, 108, 44, "REVIEW", [("product_id", "string", "PK,FK"), ("user_id", "string", "PK,FK"), ("rating", "1..5", ""), ("title / body", "string", ""), ("verified", "bool", ""), ("created_at", "datetime", "")], "ui")
    C = table(ax, 8, 98, 44, "CART", [("user_id", "string", "PK,FK"), ("items[]", "{product_id, qty}", ""), ("updated_at", "datetime", "")], "flow")
    O = table(ax, 86, 98, 44, "ORDER", [("order_id", "string", "PK"), ("user_id", "string", "FK"), ("address", "snapshot", ""), ("items[]", "snapshot lines", ""), ("pricing", "subtotal, discount, ship, GST", ""), ("total", "decimal", ""), ("status", "state", ""), ("payment", "method,status,ids", ""), ("timeline[]", "events", ""), ("coupon_code", "string", "FK")], "flow")
    PAY = table(ax, 164, 66, 44, "PAYMENT", [("gateway_order_id", "string", "PK"), ("order_id", "string", "FK"), ("amount", "paise", ""), ("status", "created..captured", ""), ("payment_id", "string", ""), ("signature", "HMAC", ""), ("last4 / network", "no card number", "")], "data")
    P = table(ax, 8, 62, 44, "PRODUCT", [("product_id", "string", "PK"), ("name / brand", "string", ""), ("category", "8 values", ""), ("subcategory", "string", ""), ("price", "decimal", ""), ("stock", "int", ""), ("image", "path", ""), ("tags[]", "string[]", ""), ("description", "text", "")], "data")
    CP = table(ax, 86, 38, 44, "COUPON", [("code", "string", "PK"), ("kind / value", "percent|flat", ""), ("min_order", "decimal", ""), ("categories[]", "string[]", ""), ("expires / limit / used", "", "")], "data")
    s = dict(arrow=False, lw=1.3, color="#334155", lfs=8, lcolor="#1e3a5f")
    line(ax, [(86, 128), (52, 128)], label="has", lpos=(69, 128), ldy=1.6, **s)
    line(ax, [(130, 136), (164, 136)], label="saves", lpos=(147, 136), ldy=1.6, **s)
    line(ax, [(130, 126), (186, 126), (186, 108)], label="writes", lpos=(158, 126), ldy=1.6, **s)
    line(ax, [(108, 120.2), (108, 98)], label="places", lpos=(108, 110), ldx=6.5, ldy=0, **s)
    line(ax, [(95, 120.2), (95, 112), (30, 112), (30, 98)], label="has one", lpos=(62, 112), ldy=1.6, **s)
    line(ax, [(30, 86.3), (30, 62)], label="refers to", lpos=(30, 74), ldx=6.5, ldy=0, **s)
    line(ax, [(130, 74), (147, 74), (147, 58), (164, 58)], label="paid by", lpos=(147, 66), ldx=6, ldy=0, **s)
    line(ax, [(96, 67.4), (96, 56), (52, 56)], label="snapshot of", lpos=(74, 56), ldy=1.6, **s)
    line(ax, [(108, 67.4), (108, 38)], label="may use", lpos=(108, 52), ldx=6.5, ldy=0, **s)
    for (x, y, t) in ((84, 129.6, "1"), (53, 129.6, "N"), (109.5, 116, "1"), (109.5, 99.6, "N"), (96.5, 114, "1"), (31.5, 99.6, "1"), (31.5, 64, "N")):
        ax.text(x, y, t, fontsize=8, fontweight="bold")
    ax.text(107.5, 8, "ORDER copies name, price and address at purchase time (snapshots), so history never changes. REVIEW and WISHLIST reference PRODUCT by product_id. One review per user per product.\n"
            "PK = primary key   FK = foreign key (enforced in application code; MongoDB has no foreign keys)", ha="center", fontsize=8, color="#475569", linespacing=1.6)
    save(fig, out)


def architecture(out):
    fig, ax = canvas(170, 126, "System Architecture", "Layered design: presentation (ui/) -> application services (shop/) -> data and AI")
    box(ax, 62, 108, 46, 8, "Customer / Administrator (browser)", "ui", 9.5, True, r=4)
    box(ax, 8, 70, 154, 30, "", "ui")
    ax.text(85, 97, "Presentation layer · Streamlit  app.py + ui/", ha="center", fontsize=10.5, fontweight="bold", color=INK)
    for i, t in enumerate(["landing", "catalog /\nproduct", "bag /\ncheckout", "payment\ndialog", "account /\norders", "admin\nconsole", "theme\n(CSS motion)"]):
        box(ax, 11 + i * 21.8, 72, 20, 14, t, "ui", 7.4, r=1)
    box(ax, 8, 32, 154, 32, "", "proc")
    ax.text(85, 61, "Application layer · Python package  shop/", ha="center", fontsize=10.5, fontweight="bold", color=INK)
    names = ["validators\nerrors", "catalog\nusers · addresses", "cart\ncoupons · pricing", "orders\nlifecycle", "payments\n(demo Razorpay)", "reviews\nwishlist", "bundles\nstats · invoice"]
    for i, t in enumerate(names):
        box(ax, 11 + i * 21.8, 34, 20, 15, t, "flow" if i in (2, 3, 4) else "proc", 7.1, r=1)
    box(ax, 8, 4, 70, 22, "", "data")
    ax.text(43, 23, "Data layer · PyMongo", ha="center", fontsize=10, fontweight="bold", color=INK)
    for i, t in enumerate(["users\naddresses", "products\nreviews", "carts\nwishlists", "orders\npayments", "coupons"]):
        box(ax, 10 + i * 13.5, 6, 12.5, 11, t, "data", 6.6, r=1)
    box(ax, 84, 4, 78, 22, "", "proc")
    ax.text(123, 23, "AI engines · scikit-learn / market-basket", ha="center", fontsize=10, fontweight="bold", color=INK)
    for i, t in enumerate(["TF-IDF +\ncosine\n(similar items)", "confidence ×\nlift\n(bought together)", "explanations\n(why this item)"]):
        box(ax, 87 + i * 25, 6, 23, 12, t, "proc", 7, r=1)
    line(ax, [(85, 108), (85, 100)], style="<|-|>", lw=1.6)
    line(ax, [(85, 70), (85, 64)], style="<|-|>", lw=1.6)
    line(ax, [(43, 32), (43, 26)], style="<|-|>", lw=1.6)
    line(ax, [(123, 32), (123, 26)], style="<|-|>", lw=1.6)
    save(fig, out)


def module_hierarchy(out):
    fig, ax = canvas(240, 140, "Module Hierarchy", "Functional decomposition: modules -> functions -> Python files")
    box(ax, 87, 122, 66, 9, "curio · AI-Based Product Recommendation System", "title", 10.5, True, r=2, color="white")
    mods = [
        ("Accounts", "ui", "shop/users.py\naddresses.py", ["Register / sign in\n(scrypt hash)", "Roles: customer,\nadmin", "Address book", "Profile, password"]),
        ("Catalogue &\nSearch", "ui", "shop/catalog.py", ["Keyword search", "Category, brand,\nprice filters", "Sort incl. best\nsellers", "Product page"]),
        ("AI\nRecommendations", "proc", "recommender.py\nbundles.py", ["Similar items\n(TF-IDF cosine)", "Bought together\n(confidence, lift)", "Reasons shown", "Fallbacks"]),
        ("Bag &\nCheckout", "flow", "cart.py coupons.py\npricing.py", ["Bag, stock limits", "Coupons (rules)", "Shipping + GST", "COD limit"]),
        ("Payments", "flow", "payments.py\n(demo Razorpay)", ["Create gateway\norder", "UPI / card / bank", "HMAC signature\nverify", "Refund"]),
        ("Orders", "flow", "orders.py\ninvoice.py", ["Reserve stock", "Status + timeline", "Cancel, expire,\nrefund", "Invoice"]),
        ("Engagement", "ui", "reviews.py\nwishlist.py", ["Reviews, verified\nbuyer", "Rating summary", "Wishlist", "Recently viewed"]),
        ("Admin", "data", "ui/admin.py\nstats.py", ["Dashboard KPIs", "Order fulfilment", "Products + photos", "Coupons"]),
    ]
    w = 28.5
    for i, (name, kind, code, funcs) in enumerate(mods):
        x = 3 + i * 29.6
        cx = x + w / 2
        line(ax, [(120, 122), (120, 116), (cx, 116), (cx, 108)], arrow=False, lw=1.1)
        box(ax, x, 96, w, 12, name, kind, 8.2, True, r=1.5)
        ax.text(cx, 91.5, code, ha="center", va="center", fontsize=6.6, family="monospace", color="#475569", linespacing=1.3)
        for j, f in enumerate(funcs):
            box(ax, x + 0.5, 70 - j * 14.5, w - 1, 12, f, kind, 6.9, r=1)
    ax.text(120, 7, "Data layer for all modules: shop/db.py (PyMongo, mongomock fallback) · shop/seed_data.py · shop/synthetic.py (bootstrap purchase history)", ha="center", fontsize=8, color="#475569")
    save(fig, out)


def usecase(out):
    fig, ax = canvas(220, 140, "UML Use Case Diagram", "Actors and system functions · dashed arrows are «include» relationships")
    ax.add_patch(Rectangle((36, 5), 148, 124, fc="#fafcff", ec="#2563a8", lw=1.4, ls="--", zorder=0))
    ax.text(110, 125, "curio · AI-Based Product Recommendation System", ha="center", fontsize=10, fontweight="bold", color="#2563a8")
    actor(ax, 16, 60, "Customer")
    actor(ax, 204, 66, "Administrator")
    actor(ax, 204, 14, "Payment\ngateway (demo)", 0.8)
    W = 36
    c1 = {"Register / sign in": 114, "Search, filter, sort": 104, "View product details": 94, "Check delivery by PIN": 84, "Add to bag / wishlist": 74,
          "Apply coupon": 64, "Checkout (address, delivery)": 54, "Pay online or COD": 44, "Track / cancel order": 34, "Write a review": 24, "Download invoice": 14}
    c2 = {"See similar products": 104, "See frequently\nbought together": 90, "Verify payment\nsignature": 44, "Reserve / release stock": 28}
    c3 = {"Manage products\nand photos": 114, "Fulfil orders\n(pack, ship, deliver)": 100, "Manage coupons": 86, "View dashboard": 72}
    pos = {}
    for d, x, k in ((c1, 66, "ui"), (c2, 108, "proc"), (c3, 150, "data")):
        for n, y in d.items():
            ellipse(ax, x, y, W, 8.6 + (1.6 if "\n" in n else 0), n, k, 7.2)
            pos[n] = (x, y)
    for n in c1:
        line(ax, [(21, 66), (66 - W / 2 + 1.5, pos[n][1])], arrow=False, lw=0.8, color="#64748b")
    for n in c3:
        line(ax, [(199, 72), (150 + W / 2 - 1.5, pos[n][1])], arrow=False, lw=0.8, color="#64748b")
    line(ax, [(199, 22), (108 + 2, 44 - 4.5)], arrow=False, lw=0.8, color="#64748b")
    inc = dict(ls="--", lw=1.0, color="#6b46a8", lcolor="#6b46a8", lfs=6.8)
    line(ax, [(66 + W / 2, 94), (108 - W / 2, 102)], **inc)
    line(ax, [(66 + W / 2, 94), (108 - W / 2, 90)], **inc)
    line(ax, [(66 + W / 2, 44), (108 - W / 2, 44)], label="«include»", ldy=1.5, **inc)
    line(ax, [(66 + W / 2, 54), (108 - W / 2, 28)], **inc)
    save(fig, out)


def class_services(out):
    fig, ax = canvas(250, 150, "UML Class Diagram - Application Services", "Package shop/ · dashed = called from the UI · solid arrows = «uses» · every service takes the MongoDB database in its constructor")
    box(ax, 85, 127, 80, 9, "ui/ + app.py  (Streamlit pages)", "ui", 9, True, r=1.5)
    W, STEP, X0 = 37, 41.3, 3
    row1 = [("UserRepository", "proc", ["+register(name,email,pw,role)", "+login(email,pw)", "+get(id) / update_name", "+change_password(old,new)"]),
            ("AddressService", "proc", ["+list / get(user,id)", "+add / update / delete", "+set_default(user,id)"]),
            ("ProductRepository", "data", ["+search(q,cat,brands,price,sort)", "+get / all / categories", "+brands / price_bounds", "+add / update / delete"]),
            ("CartService", "flow", ["+add / set_quantity", "+remove / clear", "+view(user): lines,total"]),
            ("CouponService", "flow", ["+evaluate(code, lines)", "+redeem(code)", "+create / set_active"]),
            ("OrderService", "flow", ["+create(user,addr,ship,...)", "+start_payment / confirm", "+cancel / set_status", "+expire_pending / history"])]
    ax.plot([X0 + W / 2, X0 + 5 * STEP + W / 2], [121, 121], color="#334155", lw=1.0, ls="--")
    line(ax, [(125, 127), (125, 121)], arrow=False, ls="--", lw=1.0)
    for i, (name, kind, ms) in enumerate(row1):
        x = X0 + i * STEP
        class_box(ax, x, 112, W, name, [], ms, kind, fs=6.2, lh=2.2)
        line(ax, [(x + W / 2, 121), (x + W / 2, 112)], ls="--", lw=1.0, style="->", ms=7)
    row2 = [("PaymentService", "flow", ["+create(order): rz order", "+authorize(rz,method,d)", "+bank_result(rz,ok)", "+verify_and_capture(...)", "+refund(rz)"]),
            ("DemoRazorpay", "proc", ["+create_order(paise)", "+sign / verify(HMAC)", "+authorize(method)", "test cards, UPI, banks"]),
            ("RecommenderService", "proc", ["+recommend(product_id,k)", "model cached by", "content fingerprint"]),
            ("Recommender", "proc", ["TfidfVectorizer + sparse", "+recommend(id,k,current)", "+fingerprint(products)"]),
            ("BundleService", "proc", ["+together(product_id,k)", "+popularity()", "confidence x lift"]),
            ("ReviewService /\nWishlistService", "ui", ["+add(user,pid,rating,..)", "+summary / summaries", "+toggle(user,pid)"])]
    for i, (name, kind, ms) in enumerate(row2):
        class_box(ax, X0 + i * STEP, 70, W, name.replace("\n", " "), [], ms, kind, fs=6.2, lh=2.2)
    # OrderService -> PaymentService and CouponService
    line(ax, [(X0 + 5 * STEP + W / 2, 95.4), (X0 + 5 * STEP + W / 2, 86), (X0 + W / 2, 86), (X0 + W / 2, 70)], lw=1.1, ms=8, label="uses", lpos=(120, 86), ldy=1.6, lfs=7)
    line(ax, [(X0 + 5 * STEP, 104), (X0 + 4 * STEP + W, 104)], lw=1.1, ms=8)
    line(ax, [(X0 + W, 62), (X0 + STEP, 62)], lw=1.2, ms=8)
    line(ax, [(X0 + 2 * STEP + W, 63), (X0 + 3 * STEP, 63)], lw=1.2, ms=8)
    ax.text(X0 + 2 * STEP + W + 2.1, 64.5, "builds", fontsize=5.5, ha="center", color="#1e3a5f")
    box(ax, 3, 6, 244, 24, "", "data", r=1.5)
    ax.text(125, 26, "MongoDB database  product_reco  (PyMongo)  or in-memory mongomock fallback · shop/db.py: connect(), ensure_indexes()", ha="center", fontsize=8.4, fontweight="bold", color=INK)
    for i, t in enumerate(["users (unique email)", "products", "carts · wishlists", "orders (user, status, items)", "payments", "reviews (unique user+product)", "coupons · addresses"]):
        box(ax, 6 + i * 34.4, 9, 32, 9, t, "data", 6.3, r=1)
    ax.text(125, 38, "errors.py: ShopError > ValidationError, NotFoundError, StockError, AuthError, PaymentError, DatabaseError   |   validators.py: names, emails, passwords, phones, PIN codes, cards (Luhn), UPI, reviews",
            ha="center", fontsize=6.6, color="#475569")
    save(fig, out)


def seq_payment(out):
    parts = [("Customer", "ui"), ("Checkout UI\n(Streamlit)", "ui"), ("OrderService", "flow"), ("PaymentService +\nDemoRazorpay", "flow"), ("MongoDB", "data")]
    msgs = [(0, 1, "Pay", "call"), (1, 2, "create(user, address, delivery, coupon, razorpay)", "call"),
            (2, 4, "validate stock/coupon; reserve stock (conditional $inc)", "call"), (2, 4, "insert order: status Pending Payment", "call"),
            (2, 1, "order", "ret"), (1, 2, "start_payment(order)", "call"), (2, 3, "create gateway order (amount in paise)", "call"),
            (3, 2, "order_id", "ret"), (1, 0, "secure checkout dialog (UPI / card / netbanking)", "ret"),
            (0, 1, "pay: success@razorpay  or  test card", "call"), (1, 3, "authorize(method, details)", "call"),
            (3, 3, "validate instrument (Luhn, test values)", "self"), (3, 1, "payment_id + HMAC signature", "ret"),
            (1, 2, "confirm_payment(order, result)", "call"), (2, 3, "verify signature and amount (server side)", "call"),
            (3, 2, "captured", "ret"), (2, 4, "order Placed, payment paid, timeline; redeem coupon", "call"),
            (1, 0, "confirmation page + invoice", "ret")]
    B.sequence(out, "UML Sequence Diagram - Online Payment (demo Razorpay)", "Failure paths: declined instrument or bad signature keep the order Pending Payment; unpaid orders expire after 15 minutes and release stock",
               parts, msgs, 210, 168, frames=[(2, 4, 1, 4, "alt  stock or coupon invalid -> error, nothing reserved")])


def order_lifecycle(out):
    fig, ax = canvas(210, 70, "Order Lifecycle (State Diagram)", "Transitions enforced in OrderService; stock is reserved on creation and released on cancellation or expiry")
    st = [("Pending\nPayment", 12, "dec"), ("Placed", 56, "flow"), ("Packed", 100, "flow"), ("Shipped", 144, "flow"), ("Delivered", 188, "term")]
    for t, x, k in st:
        box(ax, x - 16, 34, 32, 14, t, k, 8.5, True, r=6)
    for (a, b, lbl) in ((12, 56, "payment captured"), (56, 100, "admin: pack"), (100, 144, "admin: ship"), (144, 188, "admin: deliver")):
        line(ax, [(a + 16, 41), (b - 16, 41)], lw=1.4, label=lbl, ldy=2.3, lfs=7)
    box(ax, 70, 6, 36, 12, "Cancelled\n(stock restocked, refund if paid)", "red", 7.2, True, r=5)
    for x in (12, 56, 100):
        line(ax, [(x, 34), (x, 22), (88, 22), (88, 18)] if False else [(x, 34), (x, 12), (70, 12)], arrow=(x == 100), lw=1.0, ls="--", color="#b42318")
    ax.text(150, 12, "Customer may cancel until the order ships.\nUnpaid online orders auto-cancel after 15 minutes.", fontsize=7.5, color="#475569", linespacing=1.5)
    ax.text(12, 56, "start", fontsize=7, ha="center", color="#475569")
    save(fig, out)


def dfd1(out):
    fig, ax = canvas(220, 150, "Data Flow Diagram - Level 1", "Processes (ovals), data stores D1-D6, external entities")
    B.ent(ax, 3, 66, 26, 14, "Customer"); B.ent(ax, 191, 100, 26, 14, "Administrator"); B.ent(ax, 191, 24, 26, 14, "Payment\ngateway")
    P = {"1.0\nAccounts": (60, 128), "2.0\nBrowse &\nSearch": (60, 98), "3.0\nRecommend": (112, 98), "4.0\nBag &\nCheckout": (60, 60), "5.0\nPayments": (112, 40),
         "6.0\nOrders": (150, 72), "7.0\nAdmin": (150, 118)}
    for t, (x, y) in P.items():
        ellipse(ax, x, y, 34, 18, t, "proc" if t[0] == "3" else ("flow" if t[0] in "456" else "ui"), 7.2)
    B.store(ax, 96, 126, 30, 8, "D1", "Users+Addr")
    B.store(ax, 76, 72, 30, 8, "D2", "Products")
    B.store(ax, 30, 26, 30, 8, "D3", "Carts")
    B.store(ax, 170, 88, 30, 8, "D4", "Orders")
    B.store(ax, 80, 12, 30, 8, "D5", "Payments")
    B.store(ax, 3, 104, 28, 8, "D6", "Reviews")
    d = dict(lfs=6.4, lcolor="#334155", ms=8, lw=1.0)
    line(ax, [(29, 80), (46, 126)], style="-|>", label="sign-in", lpos=(33, 104), ldx=-1, ldy=0, **d)
    line(ax, [(29, 75), (43, 97)], style="<|-|>", **d)
    line(ax, [(29, 68), (44, 62)], style="<|-|>", **d)
    line(ax, [(77, 128), (96, 130)], style="<|-|>", **d)
    line(ax, [(60, 89), (84, 80)], style="<|-", **d); line(ax, [(112, 89), (100, 80)], style="<|-", **d)
    line(ax, [(77, 98), (95, 98)], style="<|-|>", label="product id", ldy=1.6, **d)
    line(ax, [(43, 100), (31, 106)], style="<|-|>", **d)
    line(ax, [(50, 51), (40, 34)], style="<|-|>", label="bag", lpos=(40, 44), ldx=-4, ldy=0, **d)
    line(ax, [(77, 62), (133, 70)], style="-|>", label="order request", lpos=(105, 64), ldy=1.6, **d)
    line(ax, [(138, 64), (124, 48)], style="<|-|>", **d)
    line(ax, [(129, 40), (191, 31)], style="<|-|>", label="pay / verify", lpos=(160, 36), ldy=-2, **d)
    line(ax, [(100, 32), (96, 20)], style="-|>", **d)
    line(ax, [(165, 78), (175, 88)], style="<|-|>", **d)
    line(ax, [(167, 118), (191, 110)], style="<|-|>", label="manage", lpos=(180, 119), ldy=2, **d)
    line(ax, [(150, 109), (150, 81)], style="<|-|>", **d)
    save(fig, out)


def run(OUT):
    erd(OUT / "01_erd.png")
    architecture(OUT / "02_architecture.png")
    module_hierarchy(OUT / "03_module_hierarchy.png")
    usecase(OUT / "05_use_case.png")
    class_services(OUT / "07_class_services.png")
    seq_payment(OUT / "09_sequence_payment.png")
    order_lifecycle(OUT / "10_order_lifecycle.png")
    dfd1(OUT / "13_dfd_level1.png")
