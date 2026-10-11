# Database Design & Data Dictionary

**Database:** MongoDB 7 via PyMongo, database `product_reco` (`MONGO_DB`). Schema version 4 (stored in `meta`); older demo data is rebuilt automatically on start.

Logical entities (ERD, `docs/diagrams/01_erd.png`) map to **nine collections**; cart lines, order lines, order timeline and wishlist ids are embedded arrays because they never live outside their parent.

| Collection | Purpose | Key indexes |
|---|---|---|
| `users` | accounts, roles, scrypt password hash | `email` unique |
| `addresses` | saved delivery addresses | `user_id` |
| `products` | catalogue of 125 real luxury pieces from 72 maisons (8 categories, 19 subcategories) | `category` |
| `carts` | one cart per user (`_id` = user id) | `user_id` unique |
| `wishlists` | one doc per user, `product_ids[]` | `_id` |
| `reviews` | one review per user per product | (`product_id`,`user_id`) unique |
| `coupons` | discount rules | `_id` = code |
| `orders` | orders with snapshots, pricing, payment, status, timeline | (`user_id`,`created_at`), `status`, `items.product_id` |
| `payments` | gateway order / payment records (demo Razorpay) | `order_id` |
| `meta` | schema version | – |

## users
| Field | Type | Rule |
|---|---|---|
| `_id` | string | `U-` + 8 hex |
| `name` | string | 2-60 chars, letters / space . ' - |
| `email` | string | unique, lower-case, valid format |
| `password_hash` | string | `scrypt$N$r$p$salt$digest` (N=16384, r=8, p=1, random 16-byte salt); never returned to the UI |
| `role` | string | `customer` or `admin` |
| `created_at` | datetime (UTC) | server set |

## addresses
`_id` (`A-`+8 hex), `user_id`, `label` (default Home), `name`, `phone` (10-digit Indian mobile starting 6-9), `line1` (5-120), `line2`, `city`, `state`, `pincode` (6 digits, not starting 0), `is_default` (exactly one per user).

## products
| Field | Type | Rule |
|---|---|---|
| `_id` | string | `P001`... |
| `name`, `brand`, `category` | string | 2-120 / 1-60 / 2-60 chars |
| `subcategory` | string | optional label (used only as evaluation proxy) |
| `description` | string | 10-1000 chars; feeds the recommender |
| `price` | double | > 0, 2 dp; indicative INR retail price, GST inclusive (rounded; not a live price) |
| `stock` | int | 0-100000; never negative (conditional `$inc`) |
| `source` | string | provenance of the description: `Wikipedia: <article> (CC BY-SA 4.0)` or `Written for this demo` |
| `image` | string | relative path `assets/products/<id>.jpg` (3:4 portrait) or http(s) URL |
| `tags` | string[] | <= 20, lower-case, unique; weighted x2 in TF-IDF text |

## carts / wishlists / reviews
- `carts`: `_id`=`user_id`, `items[]{product_id, quantity 1-10 <= stock}`, `updated_at`. Prices are not stored; totals use current prices.
- `wishlists`: `_id`=`user_id`, `product_ids[]`.
- `reviews`: `product_id`, `user_id`, `user_name`, `rating` 1-5, `title` 2-80, `body` 10-1500, `verified` (buyer has an active order containing the product), `created_at`.

## coupons
`_id` (code, 3-20 A-Z0-9), `kind` (`percent`|`flat`), `value`, `min_order`, `max_discount`, `categories[]` (restriction), `label`, `active`, `used`, `usage_limit`, `expires_at`. Seeded: WELCOME10 (10%, min 20,000, cap 50,000), FLAT5000 (5,000 off above 1,00,000), TIMELESS8 (8% on Watches and Jewellery above 2,00,000, cap 1,50,000), SCENT15 (15% on Fragrance above 15,000, cap 10,000).

## orders
| Field | Type | Rule |
|---|---|---|
| `_id` | string | `ORD-YYYYMMDD-XXXXXX` |
| `user_id` | string | FK users |
| `items[]` | array | snapshot `{product_id, name, brand, category, unit_price, quantity, line_total, image}` |
| `pricing` | object | `{subtotal, discount, coupon_code, shipping, shipping_method, gst_included, total}` |
| `total` | double | subtotal - discount + shipping |
| `address` | object | snapshot of the chosen address |
| `payment` | object | `{method: razorpay\|cod, status: pending\|paid\|failed\|refunded, gateway_order_id, payment_id, network, last4, bank}` |
| `status` | string | `Pending Payment` -> `Placed` -> `Packed` -> `Shipped` -> `Delivered`; `Cancelled` from the first three |
| `timeline[]` | array | `{status, at, note}` |
| `created_at`, `updated_at` | datetime | |
| `synthetic` | bool | true only for seeded history (never touches stock; hidden from revenue by default) |

## payments
`_id` (gateway order id `order_...`), `order_id`, `gateway`, `amount` (paise), `currency`, `status` (`created`|`authorized`|`captured`|`failed`|`refunded`), `method`, `payment_id` (`pay_...`), `signature` (HMAC-SHA256 of `order_id|payment_id`), `last4`/`network` (cards: **number and CVV are never stored**), timestamps.

## Integrity rules enforced in code
1. Quantity 1-10 and <= stock; stock re-checked and reserved with `update_one({_id, stock: {$gte: q}}, {$inc: {stock: -q}})`; rollback if any line fails.
2. Order lines and address are snapshots; later catalogue edits never change history.
3. Online orders reserve stock while `Pending Payment`; unpaid orders expire after 15 minutes (stock released). Cancel restocks and, if paid, refunds.
4. Payment capture re-verifies the signature and that the amount equals the order total on the server.
5. Status can only advance one step at a time and only by an admin (`require_admin`).
6. Coupons: validity, expiry, usage limit, minimum order, category restriction, discount cap; redeemed once, when payment succeeds (or at COD placement).
7. One review per user per product; one default address per user.

## Seed data
125 products (30 descriptions taken from Wikipedia, the rest written for the demo); brand facts (country, year founded) in `shop/brands.py`; 2 users (`demo@example.com`/`Demo@1234`, `admin@curio.test`/`Admin@1234`); 4 coupons; ~850 synthetic past orders generated from luxury shopping "missions" (watch collector, executive upgrade, the gift, evening, wardrobe edit, tailoring, travel...) so that "frequently bought together" has something to learn from. They are flagged `synthetic` and disclosed in the UI and docs.
