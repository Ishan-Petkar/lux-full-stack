# CURIO — AI-Based Product Recommendation System

A complete luxury e-commerce prototype (MCA project, Pimpri Chinchwad University). Real maisons and real models, an editorial storefront in the manner of a fashion house site,
and explainable recommendations. Stack: **Python · Streamlit · MongoDB (PyMongo) · Pandas · scikit-learn**.

## Quick start
```bash
./start.sh          # checks prerequisites, starts MongoDB 7 in Docker, seeds data, serves http://localhost:8501
./stop.sh           # stops the app and MongoDB (data volume kept; --purge deletes it)
```
`start.sh` verifies project files, Python >= 3.10, venv + packages (creates / installs), free ports 8501 and 27017, Docker CLI + compose + daemon (starts colima if down),
a **healthy MongoDB container**, a real MongoDB connection with seeding, and the app health URL; any failure prints the exact fix and exits non-zero.
Options: `--check` (verify only) · `--mock` (no Docker, in-memory database) · `--port N` · `--no-open`. Manual run: `pip install -r requirements.txt && streamlit run app.py`.

**Demo logins** — customer `demo@example.com` / `Demo@1234`, admin `admin@curio.test` / `Admin@1234` (buttons on the log-in page).

## The catalogue (real data)
125 luxury pieces from 72 maisons in 8 collections: **Watches, Bags, Jewellery, Fragrance, Eyewear, Apparel, Footwear, Leather & writing** — Rolex Submariner, Omega Speedmaster, Hermès Kelly,
Chanel 2.55, Cartier Love bracelet, Chanel N°5, Ray-Ban Wayfarer, Burberry trench coat, Montblanc Meisterstück and more (`scripts/catalog_master.py`).
- **Descriptions**: 30 are the opening text of the product's English Wikipedia article (CC BY-SA 4.0, fetched by `scripts/build_catalog.py`); the rest are short factual descriptions written for the demo. Each product records its `source`.
- **Maison facts** (country, year founded) from `shop/brands.py`. **Prices are indicative** (rounded, not live).
- **Photographs**: professional photography from Unsplash selected per brand / model, plus campaign imagery on the landing page. They show the piece or a very similar one, not necessarily the exact reference. Credits: `assets/CREDITS.md`.
- Two icons (Patek Philippe Nautilus, Audemars Piguet Royal Oak) are deliberately **sold out**, as in real life.

## The storefront
Modelled on the editorial minimalism of a fashion house site: a giant Didone wordmark pinned over full-bleed campaign slides (it inverts over the imagery), each slide **unfolds from a framed crop as you scroll**
(CSS scroll-driven animation), an edge-to-edge product wall, borderless tall tiles on warm grey with tiny uppercase type, a numbered category index (`[01] VIEW ALL`, `[02] WATCHES`...), a product page with a large image and a pinned
detail column, outlined `ADD` buttons. No emoji, no badges, no rounded corners; icons are thin SVG / Material. Motion is CSS only and is disabled for `prefers-reduced-motion`. Responsive from 320 px phones to 2000 px+ displays.

## Features
- **Shop**: search, collection index with subcategories, maison and price filters, sort (incl. best sellers), quick add `+`, wishlist, sold-out states, delivery estimate by PIN code.
- **AI**: *You may also like* (TF-IDF cosine similarity with reasons) and *Frequently bought together* (market-basket confidence x lift with *Add all to bag*).
- **Accounts**: scrypt-hashed passwords, customer / admin roles, address book, profile, wishlist, orders.
- **Checkout**: coupons (WELCOME10, FLAT5000, TIMELESS8, SCENT15), insured delivery (complimentary above 10,000), GST breakdown, COD (up to 50,000) or online payment.
- **Demo Razorpay gateway** (test mode clone, no real money): server-created gateway order, UPI / card / netbanking dialog, test bank page, HMAC-SHA256 signature and amount verified on the server, failure paths, refunds. Test values are on the in-app Help page.
- **Orders**: tracking timeline, cancel until dispatch (stock restored, paid orders refunded), buy again, invoice download, unpaid online orders expire after 15 minutes.
- **Admin console**: KPI dashboard, order fulfilment, products with photo upload, coupons.

## Layout
```
app.py            router + theme            ui/     landing, shop_pages (category + product), checkout (+ payment dialog), account, admin, header, components
shop/             users, addresses, catalog, cart, coupons, pricing, orders, payments, bundles, recommender, reviews, wishlist, stats, invoice,
                  synthetic, seed_data, catalog_data.json, brands, media, theme, validators, errors, db, config
scripts/          build_guide / build_report (documents), catalog_master / build_catalog / finalize_catalog (real data), unsplash_pick / fetch_product_photos (photos), evaluate, diagrams, screenshots
tests/            pytest suite (services, payments, UI journeys)       assets/  products/ hero/ CREDITS.md       docs/  diagrams, screenshots, report
start.sh stop.sh  one-command start / stop                            docker-compose.yml  MongoDB 7 with healthcheck
```

## Project deliverables
| Required item | Where it is |
|---|---|
| ERD, UML and module hierarchy | `docs/diagrams/` (ERD, module hierarchy, architecture, use case, class, sequence, state, DFD level 0 and 1) and Part 3-4 of `docs/Project_Documentation.docx` |
| User interface | Running app (`./start.sh`), 29 screenshots in `docs/screenshots/`, Part 7 of the project report |
| Database design and data dictionary | `docs/DATABASE_DESIGN.md` and Part 3 of the project report |
| Executable project with validations | This repository: `./start.sh`, validation rules in `shop/validators.py`, 158 tests |
| Beginner's guide (how everything works, with diagrams and viva questions) | `docs/Complete_Guide.docx` |
| Project report | `docs/Project_Documentation.docx` |

## Tests
```bash
pytest -q                                                                          # everything on in-memory mongomock
TEST_MONGO_URI=mongodb://localhost:27017 pytest -q --ignore=tests/test_app_ui.py   # services on real MongoDB
USE_MOCK_DB=false MONGO_DB=product_reco_uitest pytest -q tests/test_app_ui.py      # UI journeys on real MongoDB
python scripts/make_screenshots.py                                                 # real-browser end-to-end run + screenshots
python scripts/evaluate.py                                                         # recommender metrics -> docs/evaluation_results.md
```

## Known limitations
- The gateway is a **simulation** modelled on Razorpay test mode; going live means implementing the same `DemoRazorpay` methods with the `razorpay` SDK and Checkout.js plus webhooks.
- *Frequently bought together* learns from ~850 **synthetic** seeded orders (flagged `synthetic`, built from luxury shopping "missions") plus real orders placed in the app.
- Brand names are trademarks of their owners; this is a non-commercial academic demo, not affiliated with any maison. Prices are indicative; photographs may show a similar piece.
- Recommendation evaluation uses a proxy (same subcategory); see `docs/evaluation_results.md`.
- Delivery, tax and refunds are simulated; sessions live in Streamlit session state; no email or SMS.

The photo-selection scripts (`unsplash_pick.py`, `pick_sheets.py`, `photo_picks.py`) document how the images were chosen; they write temporary files to `.run/`, which is not committed.
