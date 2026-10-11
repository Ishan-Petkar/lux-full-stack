# Offline Evaluation Results

Catalog: 125 products · queries: 123 (every in-stock product) · K = 5 · random seed = 42 · scikit-learn 1.9.1 · Python 3.14.7

**Relevance proxy:** candidate is relevant if it has the same `subcategory` label as the query product (label is not a model feature). This is a conservative stand-in for independent human judgments; it says nothing about sales or user satisfaction.

## Ranking quality and coverage

| Method | P@3 | P@5 | MRR | Coverage | Empty lists |
|---|---|---|---|---|---|
| TF-IDF + cosine | 0.667 | 0.589 | 0.843 | 0.992 | 0.000 |
| Category-only baseline | 0.385 | 0.398 | 0.564 | 1.000 | 0.000 |
| Random baseline | 0.041 | 0.044 | 0.086 | 1.000 | 0.000 |

Subcategories hold 4-13 products each (19 subcategories), so small subcategories cap the attainable precision (a product with only 2 siblings can score at most 2/5). Cross-subcategory suggestions (e.g. a wallet for a watch) count as non-relevant here.

## TF-IDF Precision@5 by category

| Category | P@5 |
|---|---|
| Apparel | 0.375 |
| Bags | 0.650 |
| Eyewear | 0.956 |
| Footwear | 0.625 |
| Fragrance | 0.575 |
| Jewellery | 0.585 |
| Leather & Writing | 0.492 |
| Watches | 0.580 |

## Responsiveness (this machine, in-memory mongomock)

| Measure | ms |
|---|---|
| Feature rebuild (TF-IDF fit), mean | 1.65 |
| Similarity + ranking only, median / p95 | 0.086 / 0.101 |
| End-to-end (fetch catalog + rank), median / p95 | 0.55 / 0.62 |
