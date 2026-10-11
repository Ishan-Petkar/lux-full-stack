"""Printable tax invoice (HTML). Open it and use the browser's Print > Save as PDF."""
import html

from . import config


def _m(x: float) -> str:
    return f"{config.CURRENCY}{x:,.2f}"


def invoice_html(order: dict, customer: dict | None = None) -> str:
    e = html.escape
    a, p = order["address"], order["pricing"]
    rows = "".join(f"<tr><td>{e(i['name'])}<div class='m'>{e(i.get('brand', ''))}</div></td><td class='r'>{i['quantity']}</td>"
                   f"<td class='r'>{_m(i['unit_price'])}</td><td class='r'>{_m(i['line_total'])}</td></tr>" for i in order["items"])
    pay = order["payment"]
    method = "Cash on delivery" if pay["method"] == "cod" else "Online payment (demo Razorpay)"
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Invoice {e(order['_id'])}</title><style>
body{{font:14px/1.5 Georgia,serif;color:#18181b;max-width:760px;margin:32px auto;padding:0 20px}}
h1{{font-size:28px;margin:0}} .m{{color:#6b6b66;font-size:12px}} table{{width:100%;border-collapse:collapse;margin:18px 0}}
th,td{{padding:9px 6px;border-bottom:1px solid #e7e2d9;text-align:left}} .r{{text-align:right}} .tot td{{border:0;padding:3px 6px}}
.grand td{{font-size:18px;font-weight:700;border-top:2px solid #18181b;padding-top:10px}} .row{{display:flex;justify-content:space-between;gap:20px}}
.badge{{font:600 12px sans-serif;border:1px solid #18181b;padding:2px 8px;border-radius:99px}}
</style></head><body>
<div class="row"><div><h1>curio.</h1><div class="m">Tax invoice - academic demo store (no real sale)</div></div>
<div class="r"><b>Invoice INV-{e(order['_id'])}</b><div class="m">{order['created_at']:%d %b %Y}</div><span class="badge">{e(order['status'])}</span></div></div>
<div class="row" style="margin-top:22px"><div><b>Bill to / Ship to</b><br>{e(a['name'])}<br>{e(a['line1'])}{', ' + e(a['line2']) if a.get('line2') else ''}<br>{e(a['city'])}, {e(a['state'])} {e(a['pincode'])}<br>Phone {e(a['phone'])}</div>
<div class="r"><b>Order</b> {e(order['_id'])}<br>Payment: {method}<br>Status: {e(pay['status'])}</div></div>
<table><tr><th>Item</th><th class="r">Qty</th><th class="r">Unit price</th><th class="r">Amount</th></tr>{rows}</table>
<table class="tot"><tr><td></td><td class="r">Subtotal</td><td class="r">{_m(p['subtotal'])}</td></tr>
<tr><td></td><td class="r">Discount{(' (' + e(p['coupon_code']) + ')') if p.get('coupon_code') else ''}</td><td class="r">-{_m(p['discount'])}</td></tr>
<tr><td></td><td class="r">Shipping ({e(config.SHIPPING[p['shipping_method']]['label'])})</td><td class="r">{_m(p['shipping'])}</td></tr>
<tr class="grand"><td></td><td class="r">Total</td><td class="r">{_m(order['total'])}</td></tr>
<tr><td></td><td class="r m">Includes GST @ {int(config.GST_RATE * 100)}%</td><td class="r m">{_m(p['gst_included'])}</td></tr></table>
<p class="m">This is a computer-generated invoice for a demonstration project. No goods are shipped and no money is charged.</p>
</body></html>"""
