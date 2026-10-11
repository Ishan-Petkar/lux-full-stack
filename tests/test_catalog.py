import pytest

from shop.errors import NotFoundError, ValidationError

NEW = dict(name="Test Piece", description="A long enough description.", category="Watches", brand="Acme", price=100, stock=3, tags="a,b")


def test_seed_counts(repo):
    assert len(repo.all()) == 125
    cats = repo.categories()
    assert cats[:3] == ["Watches", "Bags", "Jewellery"] and len(cats) == 8
    assert not any("trek" in (p["category"] + p["subcategory"] + p["name"]).lower() for p in repo.all())


def test_search_keyword_brand_and_model(repo):
    assert [p["name"] for p in repo.search("submariner")] == ["Submariner"]
    assert {p["brand"] for p in repo.search("hermès")} >= {"Hermès"}
    assert repo.search("BIRKIN")


def test_search_multi_word_is_and(repo):
    res = repo.search("rolex steel")
    assert res and all("rolex" in (p["brand"] + p["name"] + p["description"] + " ".join(p["tags"])).lower() for p in res)


def test_search_special_chars_and_no_match(repo):
    assert repo.search("(((") == [] and repo.search("zzzzqqq") == []
    assert repo.search("Söhne")


def test_category_subcategory_stock_filters(repo):
    w = repo.search(category="Watches")
    assert w and {p["category"] for p in w} == {"Watches"}
    chrono = repo.search(category="Watches", subcategory="Chronographs")
    assert chrono and {p["subcategory"] for p in chrono} == {"Chronographs"}
    assert all(p["stock"] > 0 for p in repo.search(in_stock_only=True))
    assert len(repo.search(in_stock_only=True)) == len(repo.all()) - 2          # two sold-out icons
    assert "Sports watches" in repo.subcategories("Watches")


def test_sorting(repo):
    prices = [p["price"] for p in repo.search(sort="Price: low to high")]
    assert prices == sorted(prices)
    assert [p["price"] for p in repo.search(sort="Price: high to low")] == sorted(prices, reverse=True)


def test_brand_and_price_filters(repo):
    cart = repo.search(brands=["Cartier"])
    assert cart and {p["brand"] for p in cart} == {"Cartier"}
    cheap = repo.search(price_range=(0, 20000))
    assert cheap and all(p["price"] <= 20000 for p in cheap)
    lo, hi = repo.price_bounds()
    assert lo < 10000 and hi > 4_000_000
    assert "Hermès" in repo.brands("Bags")


def test_best_sellers_sort_uses_popularity(repo, P):
    res = repo.search(category="Fragrance", sort="Best sellers", popularity={P("Dior Sauvage Eau de Parfum"): 50, P("Chanel Bleu de Chanel"): 10})
    assert [p["_id"] for p in res[:2]] == [P("Dior Sauvage Eau de Parfum"), P("Chanel Bleu de Chanel")]


def test_newest_first(repo):
    assert repo.search(sort="Newest")[0]["_id"] == "P125"


def test_get_missing(repo):
    with pytest.raises(NotFoundError):
        repo.get("NOPE")


def test_add_update_delete(repo):
    p = repo.add(NEW)
    assert p["_id"].startswith("P") and repo.get(p["_id"])["name"] == "Test Piece"
    repo.update(p["_id"], {**NEW, "price": 250, "stock": 0})
    assert repo.get(p["_id"])["price"] == 250
    repo.delete(p["_id"])
    with pytest.raises(NotFoundError):
        repo.get(p["_id"])


def test_add_duplicate_id_and_invalid(repo):
    with pytest.raises(ValidationError):
        repo.add({**NEW, "product_id": "P001"})
    with pytest.raises(ValidationError):
        repo.add({**NEW, "price": -1})


def test_every_product_has_real_data(repo):
    for p in repo.all():
        assert len(p["description"]) >= 40 and p["price"] > 0 and p["tags"] and p["source"]
