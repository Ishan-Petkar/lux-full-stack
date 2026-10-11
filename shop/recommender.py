"""AI Recommendation Engine: content-based filtering with TF-IDF and cosine similarity.

Pipeline (synopsis section 8):  product attributes -> descriptive text -> TF-IDF sparse matrix
-> cosine similarity of the selected product against the catalogue -> eligibility filter -> top-N.

Because TF-IDF rows are L2-normalised, cosine similarity is a plain dot product, so only the
selected item's row is multiplied with the sparse matrix (no dense all-pairs matrix is built).
"""
import hashlib
import re
from dataclasses import dataclass, field

from sklearn.feature_extraction.text import TfidfVectorizer

from . import config


@dataclass
class Recommendation:
    product: dict
    score: float | None            # cosine similarity; None for the category fallback
    reasons: list[str] = field(default_factory=list)


@dataclass
class RecommendationResult:
    items: list[Recommendation]
    method: str                    # "content-based" | "category-fallback" | "none"
    message: str = ""


def product_text(p: dict) -> str:
    """Descriptive text used for vectorisation. Tags are repeated to give curated keywords more weight."""
    tags = " ".join(p.get("tags") or [])
    parts = [p.get("name"), p.get("category"), p.get("brand"), tags, tags, p.get("description")]
    return " ".join(str(x) for x in parts if x).strip()


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


class Recommender:
    def __init__(self, products: list[dict]):
        self.products = list(products)
        self.index = {p["_id"]: i for i, p in enumerate(self.products)}
        self.texts = [product_text(p) for p in self.products]
        self.vectorizer = TfidfVectorizer(
            stop_words="english", sublinear_tf=True,
            token_pattern=r"(?u)\b[a-zA-Z0-9][a-zA-Z0-9+\-]+\b")
        self.matrix = None
        if any(self.texts):
            try:
                self.matrix = self.vectorizer.fit_transform(self.texts)
            except ValueError:      # empty vocabulary (all texts blank / only stop-words)
                self.matrix = None

    @staticmethod
    def fingerprint(products: list[dict]) -> str:
        h = hashlib.sha1()
        for p in sorted(products, key=lambda x: x["_id"]):
            h.update(f"{p['_id']}|{product_text(p)}\n".encode())
        return h.hexdigest()

    # ---------- public ----------
    def recommend(self, product_id: str, k: int = config.TOP_N,
                  current: dict[str, dict] | None = None) -> RecommendationResult:
        """Top-k eligible products similar to ``product_id``.

        ``current`` optionally maps product id -> fresh document so stock/price changes made after
        the model was built are respected without rebuilding the vectors.
        """
        if k < 1:
            return RecommendationResult([], "none", "k must be at least 1.")
        if product_id not in self.index:
            return RecommendationResult([], "none", "This product is not part of the recommendation model yet.")

        def live(p):
            return (current or {}).get(p["_id"], p)

        base_i = self.index[product_id]
        base = live(self.products[base_i])

        def eligible(i: int) -> bool:
            p = live(self.products[i])
            return i != base_i and p.get("stock", 0) > 0 and _norm(p["name"]) != _norm(base["name"])

        scored: list[tuple[int, float]] = []
        if self.matrix is not None and self.texts[base_i]:
            sims = (self.matrix[base_i] @ self.matrix.T).toarray().ravel()
            seen: set[str] = set()
            for i in sorted(range(len(sims)), key=lambda j: (-sims[j], self.products[j]["_id"])):
                if sims[i] <= 1e-9:
                    break
                key = _norm(self.products[i]["name"])
                if eligible(i) and key not in seen:
                    seen.add(key)
                    scored.append((i, float(sims[i])))
                    if len(scored) == k:
                        break

        if scored:
            items = [Recommendation(live(self.products[i]), s, self._reasons(base, live(self.products[i])))
                     for i, s in scored]
            return RecommendationResult(items, "content-based")

        # fallback: same category, clearly labelled, no invented score
        seen = set()
        items = []
        for i, p in enumerate(self.products):
            p = live(p)
            if (p.get("category") and p.get("category") == base.get("category")
                    and eligible(i) and _norm(p["name"]) not in seen):
                seen.add(_norm(p["name"]))
                items.append(Recommendation(p, None, [f"same category: {p['category']}"]))
                if len(items) == k:
                    break
        if items:
            return RecommendationResult(
                items, "category-fallback",
                "No sufficiently similar products were found, so these come from the same category.")
        return RecommendationResult([], "none", "No similar products are available right now.")

    @staticmethod
    def _reasons(a: dict, b: dict) -> list[str]:
        reasons = []
        if a.get("category") and a.get("category") == b.get("category"):
            reasons.append(f"same category ({b['category']})")
        if a.get("brand") and a.get("brand") == b.get("brand"):
            reasons.append(f"same brand ({b['brand']})")
        shared = sorted(set(a.get("tags") or []) & set(b.get("tags") or []))
        if shared:
            reasons.append("shared tags: " + ", ".join(shared[:4]))
        if not reasons:
            reasons.append("similar description wording")
        return reasons


class RecommenderService:
    """Caches a Recommender and rebuilds it only when catalogue *content* changes."""

    def __init__(self, repo):
        self.repo = repo
        self._model: Recommender | None = None
        self._fp: str | None = None
        self.rebuilds = 0

    def _ensure(self, products):
        fp = Recommender.fingerprint(products)
        if fp != self._fp or self._model is None:
            self._model, self._fp = Recommender(products), fp
            self.rebuilds += 1
        return self._model

    def recommend(self, product_id: str, k: int = config.TOP_N) -> RecommendationResult:
        products = self.repo.all()
        model = self._ensure(products)
        return model.recommend(product_id, k, current={p["_id"]: p for p in products})
