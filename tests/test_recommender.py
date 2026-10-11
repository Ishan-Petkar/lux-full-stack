import time

from shop.recommender import Recommender, product_text


def ids(res):
    return [r.product["_id"] for r in res.items]


def test_top_n_and_excludes_self(reco, P):
    res = reco.recommend(P("Rolex Submariner"), 5)
    assert res.method == "content-based" and len(res.items) == 5 and P("Rolex Submariner") not in ids(res)
    scores = [r.score for r in res.items]
    assert all(0 < s <= 1 for s in scores) and scores == sorted(scores, reverse=True)


def test_similar_items_make_sense(reco, P):
    """Watches get watches, fragrances get fragrances, handbags get bags."""
    for label, cat in (("Omega Seamaster", "Watches"), ("Dior Sauvage Eau de Parfum", "Fragrance"), ("Hermès Kelly", "Bags"), ("Ray-Ban Wayfarer", "Eyewear")):
        res = reco.recommend(P(label), 4)
        assert sum(r.product["category"] == cat for r in res.items) >= 3, label


def test_cross_category_when_relevant(reco, db, P):
    """Items share wording across categories (e.g. a silk scarf and a cashmere scarf)."""
    cats = {r.product["category"] for r in reco.recommend(P("Hermès Silk Carré 90"), 8).items}
    assert "Apparel" in cats and len(cats) >= 1


def test_sold_out_excluded(reco, P):
    res = reco.recommend(P("Omega Seamaster"), 124)
    assert P("Patek Philippe Nautilus") not in ids(res) and P("Audemars Piguet Royal Oak") not in ids(res)


def test_stock_changes_apply_without_rebuild(reco, db, P):
    top = ids(reco.recommend(P("Omega Seamaster"), 3))[0]
    rebuilds = reco.rebuilds
    db.products.update_one({"_id": top}, {"$set": {"stock": 0}})
    assert top not in ids(reco.recommend(P("Omega Seamaster"), 3)) and reco.rebuilds == rebuilds


def test_rebuild_when_content_changes(reco, db, P):
    reco.recommend(P("Rolex Submariner"))
    n = reco.rebuilds
    db.products.update_one({"_id": P("Omega Seamaster")}, {"$set": {"description": "completely different wording about gardening"}})
    reco.recommend(P("Rolex Submariner"))
    assert reco.rebuilds == n + 1


def test_duplicates_removed(db, reco, P):
    p = db.products.find_one({"_id": P("Omega Seamaster")})
    db.products.insert_one({**p, "_id": "P900"})
    names = [r.product["name"].lower() for r in reco.recommend(P("Rolex Submariner"), 30).items]
    assert len(names) == len(set(names))


def test_unknown_product(reco):
    res = reco.recommend("NOPE")
    assert res.method == "none" and res.items == [] and res.message


def test_category_fallback_for_blank_text():
    prods = [{"_id": "A", "name": "", "category": "X", "brand": "", "tags": [], "description": "", "stock": 1},
             {"_id": "B", "name": "Other", "category": "X", "brand": "b", "tags": [], "description": "", "stock": 1}]
    assert product_text(prods[0]) == "X"
    res = Recommender(prods).recommend("A", 3)
    assert res.method == "category-fallback" and ids(res) == ["B"]


def test_fallback_has_no_invented_score():
    prods = [{"_id": "A", "name": "the", "category": "X", "brand": "", "tags": [], "description": "the of and", "stock": 1},
             {"_id": "B", "name": "other", "category": "X", "brand": "", "tags": ["zzz"], "description": "qqq", "stock": 1}]
    res = Recommender(prods).recommend("A")
    assert res.method == "category-fallback" and res.items[0].score is None and res.message


def test_empty_catalog_and_single_item():
    assert Recommender([]).recommend("A").method == "none"
    one = [{"_id": "A", "name": "solo", "category": "X", "brand": "b", "tags": [], "description": "solo item", "stock": 1}]
    assert Recommender(one).recommend("A").items == []


def test_reasons_are_explainable(reco, P):
    for r in reco.recommend(P("Rolex Submariner"), 5).items:
        assert r.reasons


def test_k_validation(reco, P):
    assert reco.recommend(P("Rolex Submariner"), 0).items == []


def test_fast_enough(reco, P):
    reco.recommend(P("Rolex Submariner"))
    t = time.perf_counter()
    for _ in range(20):
        reco.recommend(P("Rolex Submariner"))
    assert (time.perf_counter() - t) / 20 < 0.25
