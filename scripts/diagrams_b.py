"""UML (use case, class, sequence, activity) and DFD diagrams."""
from matplotlib.patches import Circle, Rectangle
from diagram_lib import *


# ------------------------------------------------------------------ use case
def usecase(out):
    fig, ax = canvas(196, 124, "UML Use Case Diagram", "Actors and system functions · dashed arrows are «include» relationships")
    ax.add_patch(Rectangle((38, 5), 118, 106, fc="#fafcff", ec="#2563a8", lw=1.4, ls="--", zorder=0))
    ax.text(97, 107, "AI-Based Product Recommendation System", ha="center", fontsize=10, fontweight="bold", color="#2563a8")
    actor(ax, 16, 52, "Customer")
    actor(ax, 180, 62, "Administrator")
    W, H = 33, 8.2
    c1 = {"Register / Sign in": 96, "Browse catalog": 86, "Search & filter products": 76, "View product details": 66,
          "Add item to cart": 52, "Update cart quantity": 42, "Remove item from cart": 32, "Place order": 22, "View order history": 12}
    c2 = {"View similar products": 66, "Generate recommendations\n(TF-IDF + cosine)": 53, "Validate stock &\nreserve items": 22}
    c3 = {"Add product": 92, "Edit price / stock /\ndescription": 80, "Delete product": 68, "View inventory": 56}
    pos = {}
    for d, x in ((c1, 63), (c2, 99), (c3, 135)):
        for name, y in d.items():
            ellipse(ax, x, y, W, H + (1.5 if "\n" in name else 0), name, "ui" if d is c1 else ("proc" if d is c2 else "data"), 7.8)
            pos[name] = (x, y)
    for n in c1:
        line(ax, [(21, 58), (63 - W / 2 + 1.5, pos[n][1])], arrow=False, lw=0.9, color="#64748b")
    for n in c3:
        line(ax, [(175, 68), (135 + W / 2 - 1.5, pos[n][1])], arrow=False, lw=0.9, color="#64748b")
    inc = dict(ls="--", lw=1.1, color="#6b46a8", lcolor="#6b46a8", lfs=7.2)
    line(ax, [(63 + W / 2, 66), (99 - W / 2, 66)], label="«include»", ldy=1.6, **inc)
    line(ax, [(99, 66 - H / 2), (99, 53 + 5)], label="«include»", ldx=7.5, ldy=0, **inc)
    line(ax, [(63 + W / 2 - 1, 22), (99 - W / 2, 22)], label="«include»", ldy=1.6, **inc)
    save(fig, out)


# ------------------------------------------------------------------ class diagrams
def _comp(ax, x, y):  # filled diamond marker (composition) at the 'whole' end
    ax.plot([x], [y], marker="D", ms=7, color="#1e293b", zorder=6)


def class_domain(out):
    fig, ax = canvas(170, 122, "UML Class Diagram — Domain Model", "Entities stored in MongoDB (collections: users, products, carts, orders; items are embedded documents)")
    U = class_box(ax, 63, 108, 44, "User", ["+user_id: str", "+name: str", "+email: str", "+created_at: datetime"], ["+sign_in(name, email)"], "ui")
    CA = class_box(ax, 8, 78, 44, "Cart", ["+user_id: str", "+updated_at: datetime", "+items: CartItem[ ]"], ["+add(product, qty)", "+set_quantity(product, qty)", "+remove(product)", "+total(): decimal"], "flow")
    OR = class_box(ax, 118, 78, 44, "Order", ["+order_id: str", "+user_id: str", "+items: OrderItem[ ]", "+total: decimal", "+status: str", "+created_at: datetime"], ["+place(cart)", "+history(user)"], "flow")
    CI = class_box(ax, 8, 40, 44, "CartItem", ["+product_id: str", "+quantity: int"], ["+subtotal(): decimal"], "flow")
    OI = class_box(ax, 118, 40, 44, "OrderItem", ["+product_id: str", "+name: str", "+unit_price: decimal", "+quantity: int", "+line_total: decimal"], [], "flow")
    P = class_box(ax, 63, 52, 44, "Product", ["+product_id: str", "+name: str", "+description: str", "+category: str", "+subcategory: str", "+brand: str", "+price: decimal", "+stock: int", "+image: str", "+tags: str[ ]"], ["+is_available(): bool", "+text(): str"], "data")
    s = dict(arrow=False, lw=1.4, color="#334155", lfs=8, lcolor="#1e3a5f")
    line(ax, [(63, 97), (30, 97), (30, CA[1] + CA[3])], label="has", lpos=(46, 97), ldy=1.5, **s)
    ax.text(58, 99, "1", fontsize=8.5); ax.text(31.5, 80, "0..1", fontsize=8.5)
    line(ax, [(107, 97), (140, 97), (140, OR[1] + OR[3])], label="places", lpos=(124, 97), ldy=1.5, **s)
    ax.text(108, 99, "1", fontsize=8.5); ax.text(141.5, 80, "0..*", fontsize=8.5)
    line(ax, [(30, CA[1]), (30, 40)], **s); _comp(ax, 30, CA[1])
    ax.text(31.5, 41.5, "1..*", fontsize=8.5); ax.text(32, 57, "items", fontsize=8, color="#1e3a5f")
    line(ax, [(140, OR[1]), (140, 40)], **s); _comp(ax, 140, OR[1])
    ax.text(141.5, 41.5, "1..*", fontsize=8.5); ax.text(142, 57, "items", fontsize=8, color="#1e3a5f")
    line(ax, [(52, 33), (63, 33)], label="refers to", lpos=(57.5, 33), ldy=2.2, **s)
    ax.text(52.5, 30.6, "0..*", fontsize=7.5); ax.text(60.5, 30.6, "1", fontsize=8)
    line(ax, [(118, 33), (107, 33)], label="refers to", lpos=(112.5, 33), ldy=2.2, **s)
    ax.text(104.5, 34.6, "1", fontsize=8); ax.text(118.5, 30.6, "0..*", fontsize=7.5)
    ax.text(85, 3.5, "◆ composition (parts live and die with the whole)   ·   OrderItem snapshots name and unit_price at purchase time",
            ha="center", fontsize=7.8, color="#475569")
    save(fig, out)


def class_service(out):
    fig, ax = canvas(236, 128, "UML Class Diagram — Application & Recommendation Layers", "Python package shop/ · «uses» = dependency, ◆ = composition, open arrow = association")
    box(ax, 82, 108, 72, 11, "app.py — Streamlit UI\n(pages: catalog · product · cart · orders · manage)", "ui", 8.5, True, r=1.5)
    T = 96
    ur = class_box(ax, 6, T, 41, "UserRepository", ["-col: Collection"], ["+sign_in(name, email)", "+get(user_id)"], "proc")
    pr = class_box(ax, 51, T, 44, "ProductRepository", ["-col: Collection"], ["+search(query, category,", "   in_stock_only, sort)", "+get(id) / all()", "+categories()", "+add / update / delete"], "data")
    rs = class_box(ax, 103, T, 44, "RecommenderService", ["-repo: ProductRepository", "-_model: Recommender", "-_fp: str  (fingerprint)"], ["+recommend(product_id, k)", "-_ensure(products)"], "proc")
    cs = class_box(ax, 151, T, 40, "CartService", ["-carts, products"], ["+add(user, product, qty)", "+set_quantity(...)", "+remove(user, product)", "+clear(user)", "+view(user): dict"], "flow")
    os_ = class_box(ax, 195, T, 40, "OrderService", ["-orders, products,", "  carts"], ["+place(user_id): dict", "+history(user_id)"], "flow")
    # bus from UI
    line(ax, [(118, 108), (118, 103)], arrow=False, ls="--", lw=1.0)
    ax.plot([26, 215], [103, 103], color="#334155", lw=1.0, ls="--")
    for x in (26, 73, 125, 171, 215):
        line(ax, [(x, 103), (x, T)], ls="--", lw=1.0, style="->")
    ax.text(14, 105, "«uses»", fontsize=7.5, color="#475569")
    R = 54
    rc = class_box(ax, 99, R, 52, "Recommender", ["-products: list", "-texts: list[str]", "-vectorizer: TfidfVectorizer", "-matrix: sparse TF-IDF"], ["+recommend(id, k, current)", "-_reasons(a, b)", "+fingerprint(products)", "product_text(p): str"], "proc")
    rr = class_box(ax, 158, R, 36, "RecommendationResult", ["+items: list", "+method: str", "+message: str"], [], "proc")
    rn = class_box(ax, 198, R, 34, "Recommendation", ["+product: dict", "+score: float|None", "+reasons: list[str]"], [], "proc")
    va = class_box(ax, 6, R, 41, "validators", ["MAX_LINE_QTY = 10"], ["clean_name / clean_email", "clean_query(q)", "clean_quantity(q)", "clean_product(dict)"], "neutral", "module")
    ex = class_box(ax, 51, R, 44, "ShopError", ["(base class)"], ["ValidationError", "NotFoundError", "StockError", "DatabaseError"], "red", "exception hierarchy")
    line(ax, [(125, T - rs[3]), (125, R)], arrow=True, style="-|>", lw=1.4, color="#334155")
    _comp(ax, 125, T - rs[3])
    ax.text(127, 55 + 20, "builds / caches", fontsize=7.5, color="#1e3a5f"); ax.text(126.5, R + 2, "0..1", fontsize=8)
    line(ax, [(103, 90), (95, 90)], style="-|>", lw=1.4, color="#334155")
    ax.text(99, 91.8, "uses", fontsize=7, ha="center", color="#1e3a5f")
    line(ax, [(151, R - 12), (158, R - 12)], style="-|>", lw=1.4, color="#334155")
    ax.text(152, R - 9.5, "creates", fontsize=7, color="#1e3a5f")
    line(ax, [(194, R - 10), (198, R - 10)], style="-|>", lw=1.4, color="#334155", arrow=True)
    ax.text(193, R - 7.5, "0..*", fontsize=7.5, ha="right")
    _comp(ax, 194, R - 10)
    box(ax, 6, 8, 224, 22, "", "data", r=1.5)
    ax.text(118, 25.5, "MongoDB  (database  product_reco)  via  PyMongo  ·  shop/db.py: connect() → MongoDB, or in-memory mongomock fallback; ensure_indexes()", ha="center", fontsize=8.6, fontweight="bold", color=INK)
    for i, t in enumerate(["users  (unique email)", "products  (index: category)", "carts  (unique user_id)", "orders  (index: user_id, created_at)"]):
        box(ax, 12 + i * 55, 11, 51, 8, t, "data", 8, r=1)
    for x in (26, 73, 167, 211):
        line(ax, [(x, 30), (x, 32)], arrow=False, lw=0.0001)
    save(fig, out)


# ------------------------------------------------------------------ sequence diagrams
def sequence(out, title, sub, parts, msgs, W, H, frames=(), notes=(), tail=3):
    fig, ax = canvas(W, H, title, sub)
    n = len(parts)
    xs = [W / (n + 1) * (i + 1) for i in range(n)]
    top = H - 17
    for x, (name, kind) in zip(xs, parts):
        box(ax, x - 14, top, 28, 7.5, name, kind, 8.3, True, r=1.2)
        ax.plot([x, x], [top, tail], color="#94a3b8", lw=1, ls=(0, (4, 3)), zorder=1)
    y = top - 8
    step = (top - 12) / (len(msgs) + 1)
    ys = []
    for m in msgs:
        ys.append(y)
        y -= step if m[3] != "gap" else step * 0.4
    for (a, b, text, kind), yy in zip(msgs, ys):
        if kind == "self":
            x = xs[a]
            ax.plot([x, x + 8, x + 8, x], [yy, yy, yy - 3.6, yy - 3.6], color="#334155", lw=1.2, zorder=3)
            ax.annotate("", xy=(x, yy - 3.6), xytext=(x + 2, yy - 3.6), arrowprops=dict(arrowstyle="-|>", color="#334155", lw=1.2, mutation_scale=9))
            ax.text(x + 9.5, yy - 1.8, text, fontsize=7.8, va="center", color=INK)
            ax.add_patch(Rectangle((x - 0.9, yy - 4.4), 1.8, 5.2, fc="#e2e8f0", ec="#64748b", lw=0.8, zorder=2))
        else:
            ret = kind == "ret"
            x1, x2 = xs[a], xs[b]
            d = 1 if x2 > x1 else -1
            line(ax, [(x1 + d * 0.9, yy), (x2 - d * 0.9, yy)], ls="--" if ret else "-", lw=1.2, style="->" if ret else "-|>", ms=9)
            ax.text((x1 + x2) / 2, yy + 1.5, text, ha="center", fontsize=7.8, color=INK, style="italic" if ret else "normal",
                    bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.85), zorder=5)
    for (i0, i1, p0, p1, label) in frames:
        y0, y1 = ys[i0] + 4.5, ys[i1] - 4.0
        ax.add_patch(Rectangle((xs[p0] - 9, y1), xs[p1] - xs[p0] + 18, y0 - y1, fc="none", ec="#b06a14", lw=1.3, zorder=4))
        ax.add_patch(Rectangle((xs[p0] - 9, y0 - 3.4), 22, 3.4, fc="#f6e6d0", ec="#b06a14", lw=1.3, zorder=4))
        ax.text(xs[p0] - 8, y0 - 1.7, label, fontsize=7.3, va="center", fontweight="bold", color="#7a4a0c", zorder=5)
    for (txt, nx, ny, nw, nh) in notes:
        box(ax, nx, ny, nw, nh, txt, "dec", 7.4, r=0.8)
    save(fig, out)


def seq_recommend(out):
    parts = [("Customer", "ui"), ("Streamlit UI\n(app.py)", "ui"), ("ProductRepository", "data"), ("RecommenderService", "proc"), ("Recommender\n(TF-IDF)", "proc"), ("MongoDB", "data")]
    msgs = [(0, 1, "select product", "call"), (1, 2, "get(product_id)", "call"), (2, 5, "products.find_one({_id})", "call"),
            (5, 2, "product document", "ret"), (2, 1, "product", "ret"),
            (1, 3, "recommend(product_id, N)", "call"), (3, 2, "all()", "call"), (2, 5, "products.find()", "call"), (5, 3, "catalogue documents", "ret"),
            (3, 3, "fingerprint changed? → rebuild TF-IDF matrix", "self"),
            (3, 4, "recommend(id, N, live products)", "call"),
            (4, 4, "cosine = row · Xᵀ; drop self, duplicates, out-of-stock", "self"),
            (4, 3, "RecommendationResult(items, scores, reasons)", "ret"), (3, 1, "result", "ret"),
            (1, 0, "product details + similar products (with reasons)", "ret")]
    sequence(out, "UML Sequence Diagram — View Product and Similar Items", "Workflow steps 2-4 of the synopsis: select product → retrieve details → calculate similarity → display", parts, msgs, 200, 150,
             frames=[(9, 9, 3, 4, "opt")])


def seq_order(out):
    parts = [("Customer", "ui"), ("Streamlit UI\n(app.py)", "ui"), ("OrderService", "flow"), ("MongoDB", "data")]
    msgs = [(0, 1, "click “Place order”", "call"), (1, 2, "place(user_id)", "call"), (2, 3, "carts.find_one({_id: user_id})", "call"),
            (3, 2, "cart items", "ret"), (2, 3, "products.find_one() for each item  (re-check stock)", "call"), (3, 2, "current price & stock", "ret"),
            (2, 1, "StockError / ValidationError", "ret"), (1, 0, "friendly error; cart is kept", "ret"),
            (2, 3, "update_one({stock ≥ qty}, {$inc: −qty}) per item", "call"), (3, 2, "modified_count = 1", "ret"),
            (2, 3, "orders.insert_one(order snapshot)", "call"), (2, 3, "carts.update_one(items = [ ])", "call"),
            (2, 1, "order (id, items, total, status)", "ret"), (1, 0, "order confirmation", "ret")]
    sequence(out, "UML Sequence Diagram — Place Order", "Stock is re-checked and reserved atomically; reservations are rolled back if anything fails", parts, msgs, 170, 164,
             frames=[(6, 7, 0, 3, "alt  stock / cart invalid"), (8, 13, 0, 3, "else  all lines valid")],
             notes=[("If any later step fails, stock already reserved is restored ($inc +qty) and nothing is stored.", 40, 3, 90, 7)], tail=13)


# ------------------------------------------------------------------ activity / flow
def activity_shopping(out):
    fig, ax = canvas(190, 176, "UML Activity Diagram — Customer Shopping Workflow", "Solid boxes = synopsis workflow · orange = validation safeguards implemented in this project")
    cx = 70
    ax.add_patch(Circle((cx, 164), 2.6, fc="#1e293b", ec="#1e293b"))
    nodes = [("Browse / search / filter catalog", 150, "ui"), ("Select a product", 139, "ui"), ("View details + similar products", 128, "ui")]
    for t, y, k in nodes:
        box(ax, cx - 23, y - 4, 46, 8, t, k, 8.5)
    line(ax, [(cx, 161.4), (cx, 154)]); line(ax, [(cx, 146), (cx, 143)]); line(ax, [(cx, 135), (cx, 132)])
    diamond(ax, cx, 113, 44, 15, "Add to cart?")
    line(ax, [(cx, 124), (cx, 120.5)])
    line(ax, [(cx + 22, 113), (122, 113), (122, 150), (cx + 23, 150)], color="#b42318", label="No: continue browsing", lpos=(122, 132), ldx=0, lcolor="#b42318", lha="center")
    ax.texts[-1].set_rotation(90)
    diamond(ax, cx, 91, 52, 15, "Quantity valid\n& in stock?")
    line(ax, [(cx, 105.5), (cx, 98.5)], label="Yes", lcolor="#2f7d4f", ldx=4, ldy=0)
    box(ax, 6, 87, 30, 8, "Show error;\nno change", "red", 8)
    line(ax, [(cx - 26, 91), (36, 91)], color="#b42318", label="No", lcolor="#b42318", ldy=1.5)
    line(ax, [(21, 95), (21, 128), (cx - 23, 128)], color="#b42318")
    box(ax, cx - 26, 62, 52, 8, "Add item; review cart & quantities", "flow", 8.5)
    line(ax, [(cx, 83.5), (cx, 70)], label="Yes", lcolor="#2f7d4f", ldx=4, ldy=0)
    diamond(ax, cx, 46, 56, 16, "Cart valid &\nstock available?")
    line(ax, [(cx, 62), (cx, 54)])
    box(ax, 4, 41, 34, 10, "Show issue;\nrevise cart", "red", 8)
    line(ax, [(cx - 28, 46), (38, 46)], color="#b42318", label="No", lcolor="#b42318", ldy=1.5)
    line(ax, [(21, 51), (21, 66), (cx - 26, 66)], color="#b42318")
    box(ax, cx - 28, 14, 56, 10, "Reserve stock · store order in MongoDB\n· empty cart", "flow", 8.2)
    line(ax, [(cx, 38), (cx, 24)], label="Yes", lcolor="#2f7d4f", ldx=4, ldy=0)
    box(ax, 126, 14, 50, 10, "Show order confirmation", "flow", 8.5)
    line(ax, [(cx + 28, 19), (126, 19)])
    ax.add_patch(Circle((151, 6), 2.8, fc="white", ec="#1e293b", lw=1.5)); ax.add_patch(Circle((151, 6), 1.7, fc="#1e293b", ec="#1e293b"))
    line(ax, [(151, 14), (151, 8.8)])
    for t, x, y in (("Orange-labelled checks (quantity, stock re-check)\nare the 'proposed safeguards' of synopsis §11.", 118, 80),):
        box(ax, x, y, 66, 12, t, "dec", 7.8)
    save(fig, out)


def activity_reco(out):
    fig, ax = canvas(210, 100, "Recommendation Pipeline (Flowchart)", "Content-based filtering with TF-IDF and cosine similarity · eligibility filter and fallback are implemented safeguards")
    row = 78
    names = [("Product attributes\n(name, category, brand,\ntags, description)", "data"), ("Prepare descriptive\ntext (tags ×2)", "proc"), ("TF-IDF sparse\nvectors\n(fit when text changes)", "proc"),
             ("Cosine similarity of\nselected item vs\ncatalogue (one row)", "proc"), ("Exclude self, duplicate\nnames, out-of-stock", "dec")]
    xs = [5 + i * 40 for i in range(5)]
    for (t, k), x in zip(names, xs):
        box(ax, x, row - 9, 34, 18, t, k, 7.8, ls="--" if k == "dec" else "-")
    for i in range(4):
        line(ax, [(xs[i] + 34, row), (xs[i + 1], row)])
    diamond(ax, 190, 40, 36, 20, "Any positive-\nsimilarity items?", 7.6)
    line(ax, [(xs[4] + 17, row - 9), (xs[4] + 17, 62), (190, 62), (190, 50)])
    box(ax, 172, 6, 36, 14, "Rank and display top-N\nwith similarity score\nand shared attributes", "ui", 7.8)
    line(ax, [(190, 30), (190, 20)], label="Yes", lcolor="#2f7d4f", ldx=4, ldy=0)
    diamond(ax, 118, 40, 38, 20, "Same-category\nitems available?", 7.6)
    line(ax, [(172, 40), (137, 40)], color="#b42318", label="No", lcolor="#b42318", ldy=1.8)
    box(ax, 99, 6, 38, 14, "Category fallback\n(clearly labelled,\nno invented score)", "dec", 7.8)
    line(ax, [(118, 30), (118, 20)], label="Yes", lcolor="#2f7d4f", ldx=4, ldy=0)
    box(ax, 20, 28, 56, 14, "Empty state:\n“No similar products available”", "red", 7.8)
    line(ax, [(99, 40), (76, 40)], color="#b42318", label="No", lcolor="#b42318", ldy=1.8)
    ax.text(105, 2.5, "sim(x, y) = xᵀy / (‖x‖₂ ‖y‖₂)", ha="center", fontsize=9, color="#334155")
    save(fig, out)


# ------------------------------------------------------------------ DFD
def ent(ax, x, y, w, h, t):
    ax.add_patch(Rectangle((x, y), w, h, fc="#f1f5f9", ec="#475569", lw=1.5, zorder=2))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=9, fontweight="bold", zorder=3)


def store(ax, x, y, w, h, i, t):
    ax.plot([x, x + w], [y + h, y + h], color="#1f8a8a", lw=1.6); ax.plot([x, x + w], [y, y], color="#1f8a8a", lw=1.6)
    ax.add_patch(Rectangle((x, y), 6, h, fc="#d3eaea", ec="none", zorder=1))
    ax.text(x + 3, y + h / 2, i, ha="center", va="center", fontsize=7.8, fontweight="bold")
    ax.text(x + 8, y + h / 2, t, ha="left", va="center", fontsize=8.2)


def dfd0(out):
    fig, ax = canvas(170, 66, "Data Flow Diagram — Level 0 (Context)")
    ellipse(ax, 85, 30, 56, 30, "0\nAI-Based Product\nRecommendation System", "proc", 9.5)
    ent(ax, 5, 21, 28, 18, "Customer"); ent(ax, 137, 21, 28, 18, "Administrator")
    d = dict(lfs=7.6, lcolor="#334155")
    line(ax, [(33, 36), (58, 36)], label="sign-in details, search criteria,\ncart actions, order request", ldy=5, **d)
    line(ax, [(58, 24), (33, 24)], label="product list & details, similar products,\ncart view, order confirmation / history", ldy=-5.6, **d)
    line(ax, [(137, 36), (112, 36)], label="product data (add / edit / delete)", ldy=3.2, **d)
    line(ax, [(112, 24), (137, 24)], label="inventory & stock list", ldy=-3.2, **d)
    save(fig, out)


def dfd1(out):
    fig, ax = canvas(204, 144, "Data Flow Diagram — Level 1", "Processes (circles), data stores D1-D4, external entities")
    ent(ax, 3, 62, 24, 14, "Customer"); ent(ax, 177, 100, 24, 14, "Administrator")
    P = {"1.0\nManage Users": (60, 125), "2.0\nManage Products": (140, 125), "3.0\nBrowse & Search": (60, 95), "4.0\nGenerate\nRecommendations": (108, 95),
         "5.0\nManage Cart": (60, 55), "6.0\nProcess Orders": (140, 55)}
    for t, (x, y) in P.items():
        ellipse(ax, x, y, 34, 17, t, "proc" if "4.0" in t else ("flow" if t[0] in "56" else "ui"), 7.6)
    store(ax, 88, 121, 30, 8, "D1", "Users")
    store(ax, 70, 71, 30, 8, "D2", "Products")
    store(ax, 46, 26, 30, 8, "D3", "Carts")
    store(ax, 168, 51, 30, 8, "D4", "Orders")
    d = dict(lfs=6.8, lcolor="#334155", ms=8, lw=1.0)
    line(ax, [(27, 73), (27, 125), (43, 125)], label="name, email", lpos=(27, 99), ldx=-0.5, ldy=0, **d); ax.texts[-1].set_rotation(90)
    line(ax, [(77, 125), (88, 125)], style="<|-|>", **d)
    line(ax, [(27, 69), (43, 93)], style="<|-|>", label="search /\nproduct list", lpos=(33, 84), ldx=-1, ldy=0, **d)
    line(ax, [(77, 95), (91, 95)], style="<|-|>", label="product id /\nsimilar", ldy=6, **d)
    line(ax, [(27, 64), (43, 57)], style="<|-|>", label="cart actions / view", lpos=(35, 60), ldy=-3.5, ldx=0, **d)
    line(ax, [(15, 62), (15, 10), (140, 10), (140, 46.5)], style="<|-|>", label="place order / confirmation", lpos=(75, 10), ldy=1.8, **d)
    line(ax, [(60, 86.5), (74, 79)], style="<|-", **d); line(ax, [(108, 86.5), (96, 79)], style="<|-", **d)
    ax.text(60, 80.5, "read", fontsize=6.8, color="#334155"); ax.text(103, 80.5, "read", fontsize=6.8, color="#334155")
    line(ax, [(60, 46.5), (60, 34)], style="<|-|>", **d)
    line(ax, [(76, 30), (110, 30), (110, 52), (123, 53)], style="-|>", label="cart items", lpos=(94, 30), ldy=1.8, **d)
    line(ax, [(123, 58), (84, 58), (84, 71)], style="-|>", label="reserve stock", lpos=(104, 58), ldy=1.8, **d)
    line(ax, [(157, 55), (168, 55)], **d)
    line(ax, [(140, 116.5), (140, 75), (100, 75)], style="<|-|>", label="add / edit / delete", lpos=(140, 100), ldx=-1, ldy=0, **d); ax.texts[-1].set_rotation(90)
    line(ax, [(177, 107), (157, 123)], style="<|-|>", label="product data /\ninventory", lpos=(167, 120), ldy=-2, ldx=6, **d)
    save(fig, out)


def run(OUT):
    usecase(OUT / "05_use_case.png")
    class_domain(OUT / "06_class_domain.png")
    class_service(OUT / "07_class_services.png")
    seq_recommend(OUT / "08_sequence_recommend.png")
    seq_order(OUT / "09_sequence_place_order.png")
    activity_shopping(OUT / "10_activity_shopping.png")
    activity_reco(OUT / "11_flow_recommendation.png")
    dfd0(OUT / "12_dfd_level0.png")
    dfd1(OUT / "13_dfd_level1.png")
