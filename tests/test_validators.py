import pytest

from shop import validators as v
from shop.errors import ValidationError


@pytest.mark.parametrize("bad", ["", "a", "123", "x" * 80, None, "Bob<script>"])
def test_bad_names(bad):
    with pytest.raises(ValidationError):
        v.clean_name(bad)


def test_good_name_normalised():
    assert v.clean_name("  Asha   Patil ") == "Asha Patil"


@pytest.mark.parametrize("bad", ["", "plain", "a@b", "a@b.c", "@x.com", "a b@x.com", None])
def test_bad_emails(bad):
    with pytest.raises(ValidationError):
        v.clean_email(bad)


def test_email_lowercased():
    assert v.clean_email(" A.B@Example.COM ") == "a.b@example.com"


@pytest.mark.parametrize("bad", [0, -1, 1.5, "abc", None, True, 11])
def test_bad_quantity(bad):
    with pytest.raises(ValidationError):
        v.clean_quantity(bad)


def test_good_quantity():
    assert v.clean_quantity("3") == 3 and v.clean_quantity(2.0) == 2


def test_query_too_long():
    with pytest.raises(ValidationError):
        v.clean_query("x" * 101)


GOOD = dict(name="Test Item", description="A long enough description.", category="Bags",
            brand="Acme", price="199.5", stock="4", tags="Alpha, beta ,ALPHA")


def test_product_ok():
    p = v.clean_product(GOOD)
    assert p["price"] == 199.5 and p["stock"] == 4 and p["tags"] == ["alpha", "beta"]


@pytest.mark.parametrize("field,value", [("price", 0), ("price", "abc"), ("price", -5), ("stock", -1),
                                         ("stock", 2.5), ("stock", "x"), ("name", ""), ("description", "short"),
                                         ("category", ""), ("brand", "")])
def test_product_rejects(field, value):
    with pytest.raises(ValidationError):
        v.clean_product({**GOOD, field: value})
