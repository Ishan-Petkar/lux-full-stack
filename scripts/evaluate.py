"""Offline evaluation of the recommender (synopsis section 10 'Proposed Offline Evaluation').

Relevance proxy: a candidate is *relevant* when it has the same ``subcategory`` label as the query
product. This label is NOT a feature of the model. It is a stand-in for the independent human
judgments the synopsis proposes; it is conservative (cross-subcategory suggestions such as a laptop
backpack for a laptop count as non-relevant) and does not measure sales or satisfaction.

Usage: python scripts/evaluate.py [--seed 42]
"""
import argparse
import json
import random
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import mongomock  # noqa: E402
import sklearn  # noqa: E402

from shop.recommender import Recommender, RecommenderService  # noqa: E402
from shop.catalog import ProductRepository  # noqa: E402
from shop.seed_data import seed_if_empty  # noqa: E402


def metrics(rank_lists, queries, by_id, ks):
    """rank_lists: {query_id: [product_id,...]}  ->  dict of P@K, MRR, coverage, empty-rate."""
    out = {}
    for k in ks:
        precs = []
        for q in queries:
            got = rank_lists[q][:k]
            rel = sum(by_id[i]["subcategory"] == by_id[q]["subcategory"] for i in got)
            precs.append(rel / len(got) if got else 0.0)      # empty list scores 0; denominator = returned count
        out[f"P@{k}"] = statistics.mean(precs)
    rr = []
    for q in queries:
        score = 0.0
        for r, i in enumerate(rank_lists[q], 1):
            if by_id[i]["subcategory"] == by_id[q]["subcategory"]:
                score = 1 / r
                break
        rr.append(score)
    out["MRR"] = statistics.mean(rr)
    shown = {i for q in queries for i in rank_lists[q]}
    eligible = [p for p in by_id.values() if p["stock"] > 0]
    out["Coverage"] = len(shown & {p["_id"] for p in eligible}) / len(eligible)
    out["Empty lists"] = sum(1 for q in queries if not rank_lists[q]) / len(queries)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args()
    ks = sorted({3, args.k})

    db = mongomock.MongoClient()["eval"]
    seed_if_empty(db)
    repo = ProductRepository(db)
    products = repo.all()
    by_id = {p["_id"]: p for p in products}
    queries = [p["_id"] for p in products if p["stock"] > 0]        # every in-stock product is a query
    pool = lambda q: [p["_id"] for p in products if p["stock"] > 0 and p["_id"] != q]

    # --- TF-IDF recommender
    model = Recommender(products)
    tfidf = {q: [r.product["_id"] for r in model.recommend(q, args.k).items] for q in queries}

    # --- baselines: same candidate pool, same K
    rng = random.Random(args.seed)
    rand = {q: rng.sample(pool(q), args.k) for q in queries}
    cat_only = {}
    for q in queries:
        same = [i for i in pool(q) if by_id[i]["category"] == by_id[q]["category"]]
        cat_only[q] = rng.sample(same, min(args.k, len(same)))

    results = {"TF-IDF + cosine": metrics(tfidf, queries, by_id, ks),
               "Category-only baseline": metrics(cat_only, queries, by_id, ks),
               "Random baseline": metrics(rand, queries, by_id, ks)}

    # --- per-category P@K for TF-IDF
    per_cat = {}
    for cat in sorted({p["category"] for p in products}):
        qs = [q for q in queries if by_id[q]["category"] == cat]
        per_cat[cat] = metrics({q: tfidf[q] for q in qs}, qs, by_id, ks)["P@%d" % args.k]

    # --- responsiveness: feature building measured separately from per-request latency
    t = time.perf_counter()
    for _ in range(20):
        Recommender(products)
    build_ms = (time.perf_counter() - t) / 20 * 1000
    svc = RecommenderService(repo)
    svc.recommend(queries[0])
    lat = []
    for _ in range(5):
        for q in queries:
            t = time.perf_counter()
            svc.recommend(q, args.k)
            lat.append((time.perf_counter() - t) * 1000)
    lat.sort()
    model_lat = []
    for q in queries:
        t = time.perf_counter()
        model.recommend(q, args.k)
        model_lat.append((time.perf_counter() - t) * 1000)
    model_lat.sort()
    pct = lambda xs, p: xs[min(len(xs) - 1, int(p * len(xs)))]

    env = {"catalog_size": len(products), "queries": len(queries), "K": args.k, "seed": args.seed,
           "scikit-learn": sklearn.__version__, "python": sys.version.split()[0],
           "features": "name + category + brand + tags(x2) + description; TfidfVectorizer(stop_words=english, sublinear_tf=True)"}
    resp = {"feature_build_ms_mean": build_ms,
            "model_only_ms_median": statistics.median(model_lat), "model_only_ms_p95": pct(model_lat, 0.95),
            "end_to_end_ms_median": statistics.median(lat), "end_to_end_ms_p95": pct(lat, 0.95)}

    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "evaluation_results.json").write_text(json.dumps(
        {"environment": env, "results": results, "per_category": per_cat, "responsiveness": resp}, indent=2))

    cols = [f"P@{k}" for k in ks] + ["MRR", "Coverage", "Empty lists"]
    md = ["# Offline Evaluation Results", "",
          f"Catalog: {env['catalog_size']} products · queries: {env['queries']} (every in-stock product) · K = {args.k} · "
          f"random seed = {args.seed} · scikit-learn {env['scikit-learn']} · Python {env['python']}", "",
          "**Relevance proxy:** candidate is relevant if it has the same `subcategory` label as the query product "
          "(label is not a model feature). This is a conservative stand-in for independent human judgments; "
          "it says nothing about sales or user satisfaction.", "",
          "## Ranking quality and coverage", "",
          "| Method | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
    for name, r in results.items():
        md.append(f"| {name} | " + " | ".join(f"{r[c]:.3f}" for c in cols) + " |")
    sizes = {}
    for p_ in products:
        sizes[p_["subcategory"]] = sizes.get(p_["subcategory"], 0) + 1
    md += ["", f"Subcategories hold {min(sizes.values())}-{max(sizes.values())} products each ({len(sizes)} subcategories), so small subcategories cap the attainable precision "
               f"(a product with only 2 siblings can score at most 2/{args.k}). Cross-subcategory suggestions (e.g. a wallet for a watch) count as non-relevant here.", "",
           f"## TF-IDF Precision@{args.k} by category", "", "| Category | P@%d |" % args.k, "|---|---|"]
    md += [f"| {c} | {v:.3f} |" for c, v in per_cat.items()]
    md += ["", "## Responsiveness (this machine, in-memory mongomock)", "",
           "| Measure | ms |", "|---|---|",
           f"| Feature rebuild (TF-IDF fit), mean | {resp['feature_build_ms_mean']:.2f} |",
           f"| Similarity + ranking only, median / p95 | {resp['model_only_ms_median']:.3f} / {resp['model_only_ms_p95']:.3f} |",
           f"| End-to-end (fetch catalog + rank), median / p95 | {resp['end_to_end_ms_median']:.2f} / {resp['end_to_end_ms_p95']:.2f} |"]
    (ROOT / "docs" / "evaluation_results.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
