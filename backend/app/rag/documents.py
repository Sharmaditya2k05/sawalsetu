"""Turn MargBooks records into retrievable documents.

Two kinds of documents are produced:

1. Record documents - one per bill / order / ledger / item, written as a short natural
   language passage so lexical and dense retrieval both work on them.
2. Analytics documents - pre-computed aggregates (monthly sales, customer and supplier
   profiles, receivables ageing, business snapshot). Plain RAG over raw rows is poor at
   "what were my sales in October", so we materialise the numbers at sync time and let the
   model quote them with a citation.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Iterable

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]


@dataclass
class Document:
    id: str
    text: str
    kind: str                      # sale_bill | purchase_bill | ledger | item | analytics | ...
    title: str
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------- helpers

def inr(value: float | int | None) -> str:
    """Format a number as Indian rupees with lakh/crore grouping."""
    if value is None:
        return "₹0"
    value = float(value)
    sign = "-" if value < 0 else ""
    value = abs(value)
    whole = int(round(value))
    s = str(whole)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return f"{sign}₹{s}"


def short_inr(value: float) -> str:
    v = abs(float(value))
    if v >= 1e7:
        return f"₹{value / 1e7:.2f} Cr"
    if v >= 1e5:
        return f"₹{value / 1e5:.2f} L"
    return inr(value)


def parse_date(raw: str | None) -> date | None:
    if not raw:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw[:19], fmt).date()
        except ValueError:
            continue
    return None


def month_key(d: date) -> str:
    return f"{d.year}-{d.month:02d}"


def month_label(key: str) -> str:
    y, m = key.split("-")
    return f"{MONTHS[int(m) - 1]} {y}"


def fy_label(d: date) -> str:
    start = d.year if d.month >= 4 else d.year - 1
    return f"FY {start}-{str(start + 1)[-2:]}"


# ---------------------------------------------------------------- record documents

def bill_document(rec: dict, kind: str, company: str) -> Document:
    d = parse_date(rec.get("billDate"))
    label = {
        "sale_bill": "Sales invoice", "sale_order": "Sales order", "sale_challan": "Delivery challan",
        "purchase_bill": "Purchase bill", "purchase_order": "Purchase order",
        "purchase_challan": "Purchase challan", "purchase_return": "Purchase return",
    }[kind]
    party_role = "supplier" if kind.startswith("purchase") else "customer"
    amount = rec.get("totalAmount") or rec.get("totalItemsAmount") or 0
    date_txt = f"{d.day} {MONTHS[d.month - 1]} {d.year}" if d else "unknown date"
    parts = [
        f"{label} {rec.get('billNo') or rec.get('uniqueId')} dated {date_txt}",
        f"({month_label(month_key(d))}, {fy_label(d)})" if d else "",
        f"for {party_role} {rec.get('ledgerName')}.",
        f"Amount {inr(amount)}, quantity {rec.get('totalQty', 0)} units.",
    ]
    if rec.get("totalDiscount"):
        parts.append(f"Discount {inr(rec['totalDiscount'])}.")
    if rec.get("creditDays"):
        parts.append(f"Credit period {rec['creditDays']} days.")
    status = rec.get("status")
    if status:
        parts.append(f"Payment status: {status}.")
        if status == "Pending" and d:
            parts.append(f"Outstanding since {date_txt}.")
    if rec.get("remarks"):
        parts.append(f"Remarks: {rec['remarks']}.")
    if rec.get("storeId"):
        parts.append(f"Store id {rec['storeId']}.")
    return Document(
        id=f"{kind}:{rec.get('uniqueId')}",
        text=" ".join(p for p in parts if p),
        kind=kind,
        title=f"{label} {rec.get('billNo') or ''}".strip(),
        metadata={
            "date": d.isoformat() if d else None, "month": month_key(d) if d else None,
            "party": rec.get("ledgerName"), "amount": float(amount or 0), "status": status,
            "billNo": rec.get("billNo"),
        },
    )


def ledger_document(rec: dict) -> Document:
    kind = rec.get("ledgerKind") or ("supplier" if rec.get("accountGroupId") == 201 else "customer")
    parts = [f"Ledger / party master: {rec.get('name')}"]
    if rec.get("alias") and rec.get("alias") != rec.get("name"):
        parts.append(f"(alias {rec['alias']})")
    parts.append(f"is a {kind} account.")
    loc = ", ".join(str(x) for x in (rec.get("address1"), rec.get("address2"), rec.get("city")) if x)
    if loc:
        parts.append(f"Address: {loc}.")
    if rec.get("creditLimit"):
        parts.append(f"Credit limit {inr(rec['creditLimit'])}.")
    if rec.get("creditLimitDays"):
        parts.append(f"Credit terms {rec['creditLimitDays']} days.")
    if rec.get("openingBalance"):
        parts.append(f"Opening balance {inr(rec['openingBalance'])}.")
    if rec.get("pan"):
        parts.append(f"PAN {rec['pan']}.")
    return Document(
        id=f"ledger:{rec.get('uniqueId')}", text=" ".join(parts), kind="ledger",
        title=f"Party: {rec.get('name')}", metadata={"party": rec.get("name"), "ledgerKind": kind},
    )


def item_document(rec: dict) -> Document:
    name = rec.get("product") or rec.get("printName") or rec.get("itemCode")
    parts = [f"Item master: {name}"]
    if rec.get("itemCode"):
        parts.append(f"(code {rec['itemCode']})")
    if rec.get("companyName"):
        parts.append(f"by {rec['companyName']}")
    parts.append(".")
    if rec.get("unit"):
        parts.append(f"Unit {rec['unit']}.")
    if rec.get("mrp"):
        parts.append(f"MRP {inr(rec['mrp'])}.")
    if rec.get("cost"):
        parts.append(f"Purchase cost {inr(rec['cost'])}.")
        if rec.get("mrp"):
            margin = (float(rec["mrp"]) - float(rec["cost"])) / float(rec["mrp"]) * 100
            parts.append(f"Margin on MRP {margin:.1f}%.")
    if rec.get("hsn"):
        parts.append(f"HSN {rec['hsn']}.")
    if rec.get("category"):
        parts.append(f"Category {rec['category']}.")
    if rec.get("minimumQuantity"):
        parts.append(f"Minimum stock level {rec['minimumQuantity']}, reorder quantity {rec.get('reorderQuantity', 0)}.")
    if rec.get("scheduleH"):
        parts.append("Schedule H drug (prescription required).")
    return Document(
        id=f"item:{rec.get('uniqueId')}", text=" ".join(parts).replace(" .", "."), kind="item",
        title=f"Item: {name}", metadata={"item": name, "company": rec.get("companyName")},
    )


def ecom_order_document(rec: dict) -> Document:
    d = parse_date(rec.get("orderDate"))
    items = ", ".join(f"{i.get('skuName')} x{i.get('uomQty') or i.get('order_Qty')}" for i in rec.get("items") or [])
    date_txt = f"{d.day} {MONTHS[d.month - 1]} {d.year}" if d else "unknown date"
    text = (
        f"E-commerce order {rec.get('orderNo')} from {rec.get('orderSource')} dated {date_txt}"
        f"{' (' + month_label(month_key(d)) + ')' if d else ''}. Customer {rec.get('customerName')}, "
        f"payment {rec.get('paymentMethod')}, status {rec.get('status')}, amount {inr(rec.get('orderAmount'))}. "
        f"Items: {items}."
    )
    return Document(
        id=f"ecom:{rec.get('orderId')}", text=text, kind="ecom_order",
        title=f"{rec.get('orderSource')} order {rec.get('orderNo')}",
        metadata={"date": d.isoformat() if d else None, "month": month_key(d) if d else None,
                  "channel": rec.get("orderSource"), "amount": float(rec.get("orderAmount") or 0)},
    )


# ---------------------------------------------------------------- analytics documents

def _group_by_month(records: Iterable[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        d = parse_date(r.get("billDate"))
        if d:
            out[month_key(d)].append(r)
    return dict(sorted(out.items()))


def _amount(r: dict) -> float:
    return float(r.get("totalAmount") or r.get("totalItemsAmount") or 0)


def analytics_documents(data: dict[str, list[dict]], company: str, today: date) -> tuple[list[Document], dict]:
    docs: list[Document] = []
    sales = data.get("sale_bills", [])
    purchases = data.get("purchase_bills", [])
    returns = data.get("purchase_returns", [])
    ecom = data.get("ecom_orders", [])

    sales_by_month = _group_by_month(sales)
    purchases_by_month = _group_by_month(purchases)

    # -- monthly sales ---------------------------------------------------------
    prev_total = None
    monthly_series = []
    for mk, rows in sales_by_month.items():
        total = sum(_amount(r) for r in rows)
        qty = sum(int(r.get("totalQty") or 0) for r in rows)
        by_party: dict[str, float] = defaultdict(float)
        for r in rows:
            by_party[r.get("ledgerName") or "Unknown"] += _amount(r)
        top = sorted(by_party.items(), key=lambda kv: kv[1], reverse=True)[:5]
        pending = [r for r in rows if r.get("status") == "Pending"]
        pending_amt = sum(_amount(r) for r in pending)
        cash = sum(_amount(r) for r in rows if r.get("ledgerName") == "Cash Account")
        growth = ""
        if prev_total:
            pct = (total - prev_total) / prev_total * 100
            growth = f" That is {'up' if pct >= 0 else 'down'} {abs(pct):.1f}% versus the previous month ({inr(prev_total)})."
        purchase_total = sum(_amount(r) for r in purchases_by_month.get(mk, []))
        text = (
            f"Monthly sales summary for {month_label(mk)} ({fy_label(date(int(mk[:4]), int(mk[5:]), 1))}) at {company}: "
            f"total sales {inr(total)} across {len(rows)} invoices, {qty} units sold, average invoice value "
            f"{inr(total / len(rows)) if rows else inr(0)}.{growth} Counter (cash) sales were {inr(cash)}. "
            f"Top customers in {month_label(mk)}: " + "; ".join(f"{p} {inr(a)}" for p, a in top) + ". "
            f"{len(pending)} invoices worth {inr(pending_amt)} from this month are still unpaid. "
            f"Purchases in the same month were {inr(purchase_total)}, giving a gross sales-to-purchase gap of "
            f"{inr(total - purchase_total)}."
        )
        docs.append(Document(id=f"analytics:sales:{mk}", text=text, kind="analytics",
                             title=f"Sales summary – {month_label(mk)}",
                             metadata={"month": mk, "total": total, "invoices": len(rows)}))
        monthly_series.append({"month": mk, "label": month_label(mk)[:3] + " " + mk[2:4], "sales": round(total, 2),
                               "purchases": round(purchase_total, 2), "invoices": len(rows)})
        prev_total = total

    # -- monthly purchases ------------------------------------------------------
    for mk, rows in purchases_by_month.items():
        total = sum(_amount(r) for r in rows)
        by_party: dict[str, float] = defaultdict(float)
        for r in rows:
            by_party[r.get("ledgerName") or "Unknown"] += _amount(r)
        top = sorted(by_party.items(), key=lambda kv: kv[1], reverse=True)[:5]
        pending_amt = sum(_amount(r) for r in rows if r.get("status") == "Pending")
        text = (
            f"Monthly purchase summary for {month_label(mk)} at {company}: total purchases {inr(total)} across "
            f"{len(rows)} supplier bills. Top suppliers: " + "; ".join(f"{p} {inr(a)}" for p, a in top) +
            f". Supplier bills still payable from this month: {inr(pending_amt)}."
        )
        docs.append(Document(id=f"analytics:purchases:{mk}", text=text, kind="analytics",
                             title=f"Purchase summary – {month_label(mk)}", metadata={"month": mk, "total": total}))

    # -- customer profiles ------------------------------------------------------
    customers: dict[str, list[dict]] = defaultdict(list)
    for r in sales:
        customers[r.get("ledgerName") or "Unknown"].append(r)
    ledger_by_name = {l.get("name"): l for l in data.get("ledgers", [])}
    total_sales_all = sum(_amount(r) for r in sales) or 1
    ranked_customers = sorted(customers.items(), key=lambda kv: sum(_amount(r) for r in kv[1]), reverse=True)
    receivables_rows = []
    for rank, (name, rows) in enumerate(ranked_customers, start=1):
        total = sum(_amount(r) for r in rows)
        pending = [r for r in rows if r.get("status") == "Pending"]
        pending_amt = sum(_amount(r) for r in pending)
        dates = sorted(d for d in (parse_date(r.get("billDate")) for r in rows) if d)
        last = dates[-1] if dates else None
        first = dates[0] if dates else None
        oldest_pending = min((parse_date(r.get("billDate")) for r in pending), default=None)
        ledger = ledger_by_name.get(name, {})
        credit_days = ledger.get("creditLimitDays") or (rows[0].get("creditDays") if rows else 0)
        overdue = [r for r in pending if (today - parse_date(r["billDate"])).days > (credit_days or 0)]
        overdue_amt = sum(_amount(r) for r in overdue)
        months_active = max(1, len({month_key(d) for d in dates}))
        text = (
            f"Customer profile: {name}. Rank #{rank} by sales at {company} with lifetime billing of {inr(total)} "
            f"({total / total_sales_all * 100:.1f}% of all sales) across {len(rows)} invoices, averaging "
            f"{inr(total / months_active)} per active month. First invoice {first.strftime('%d %b %Y') if first else 'n/a'}, "
            f"most recent invoice {last.strftime('%d %b %Y') if last else 'n/a'}. "
            f"Credit terms {credit_days} days, credit limit {inr(ledger.get('creditLimit') or 0)}. "
            f"Outstanding (unpaid) amount {inr(pending_amt)} across {len(pending)} invoices"
            + (f", of which {inr(overdue_amt)} across {len(overdue)} invoices is overdue beyond credit terms" if overdue else "")
            + (f"; oldest unpaid invoice dated {oldest_pending.strftime('%d %b %Y')}" if oldest_pending else "") + "."
            + (f" Location: {ledger.get('city') or ledger.get('address2')}." if ledger.get("city") or ledger.get("address2") else "")
        )
        docs.append(Document(id=f"analytics:customer:{name}", text=text, kind="analytics",
                             title=f"Customer profile – {name}",
                             metadata={"party": name, "total": total, "pending": pending_amt, "rank": rank}))
        if pending_amt > 0 and name != "Cash Account":
            receivables_rows.append({"party": name, "pending": round(pending_amt, 2), "overdue": round(overdue_amt, 2),
                                     "invoices": len(pending), "oldest": oldest_pending.isoformat() if oldest_pending else None})

    # -- customer ranking -------------------------------------------------------
    ranked_named = [(n, rows) for n, rows in ranked_customers if n != "Cash Account"]
    text = (
        f"Top customers ranked by sales at {company} ({month_label(next(iter(sales_by_month), month_key(today)))} to "
        f"{month_label(next(reversed(sales_by_month), month_key(today)))}). Top 10 customers by total billing: "
        + "; ".join(
            f"#{i} {n} {inr(sum(_amount(r) for r in rows))} ({len(rows)} invoices, pending "
            f"{inr(sum(_amount(r) for r in rows if r.get('status') == 'Pending'))})"
            for i, (n, rows) in enumerate(ranked_named[:10], start=1)
        )
        + f". The top 5 customers together account for "
        f"{sum(_amount(r) for _, rows in ranked_named[:5] for r in rows) / total_sales_all * 100:.1f}% of sales."
    )
    docs.append(Document(id="analytics:top_customers", text=text, kind="analytics",
                         title="Top customers by sales", metadata={}))

    # -- supplier profiles ------------------------------------------------------
    suppliers: dict[str, list[dict]] = defaultdict(list)
    for r in purchases:
        suppliers[r.get("ledgerName") or "Unknown"].append(r)
    returns_by_supplier: dict[str, list[dict]] = defaultdict(list)
    for r in returns:
        returns_by_supplier[r.get("ledgerName") or "Unknown"].append(r)
    total_purchase_all = sum(_amount(r) for r in purchases) or 1
    payables_total = 0.0
    for rank, (name, rows) in enumerate(sorted(suppliers.items(), key=lambda kv: sum(_amount(r) for r in kv[1]), reverse=True), 1):
        total = sum(_amount(r) for r in rows)
        pending_amt = sum(_amount(r) for r in rows if r.get("status") == "Pending")
        payables_total += pending_amt
        rets = returns_by_supplier.get(name, [])
        ret_amt = sum(_amount(r) for r in rets)
        reasons = sorted({r.get("remarks") for r in rets if r.get("remarks")})
        last = max((parse_date(r.get("billDate")) for r in rows), default=None)
        text = (
            f"Supplier profile: {name}. Rank #{rank} by purchase value at {company}: {inr(total)} "
            f"({total / total_purchase_all * 100:.1f}% of purchases) over {len(rows)} bills, last bill "
            f"{last.strftime('%d %b %Y') if last else 'n/a'}. Amount payable (unpaid bills) {inr(pending_amt)}. "
            f"Purchase returns to this supplier: {len(rets)} worth {inr(ret_amt)}"
            + (f" (reasons: {', '.join(reasons)})" if reasons else "") + "."
        )
        docs.append(Document(id=f"analytics:supplier:{name}", text=text, kind="analytics",
                             title=f"Supplier profile – {name}", metadata={"party": name, "total": total}))

    ranked_suppliers = sorted(suppliers.items(), key=lambda kv: sum(_amount(r) for r in kv[1]), reverse=True)
    text = (
        f"Top suppliers ranked by purchase value at {company}: "
        + "; ".join(
            f"#{i} {n} {inr(sum(_amount(r) for r in rows))} ({len(rows)} bills, payable "
            f"{inr(sum(_amount(r) for r in rows if r.get('status') == 'Pending'))})"
            for i, (n, rows) in enumerate(ranked_suppliers[:10], start=1)
        )
        + f". Total payable to suppliers (unpaid purchase bills): {inr(payables_total)}."
    )
    docs.append(Document(id="analytics:top_suppliers", text=text, kind="analytics",
                         title="Top suppliers by purchases", metadata={}))

    # -- receivables ageing -----------------------------------------------------
    buckets = {"0-30 days": 0.0, "31-60 days": 0.0, "61-90 days": 0.0, "over 90 days": 0.0}
    bucket_counts = {k: 0 for k in buckets}
    pending_all = [r for r in sales if r.get("status") == "Pending" and r.get("ledgerName") != "Cash Account"]
    for r in pending_all:
        age = (today - parse_date(r["billDate"])).days
        key = "0-30 days" if age <= 30 else "31-60 days" if age <= 60 else "61-90 days" if age <= 90 else "over 90 days"
        buckets[key] += _amount(r)
        bucket_counts[key] += 1
    receivables_total = sum(buckets.values())
    receivables_rows.sort(key=lambda x: x["pending"], reverse=True)
    text = (
        f"Party-wise receivables (outstanding / udhaar / debtors) ageing report for {company} as of {today.strftime('%d %b %Y')}. "
        f"Which party has the highest outstanding: {receivables_rows[0]['party'] if receivables_rows else 'none'} with "
        f"{inr(receivables_rows[0]['pending']) if receivables_rows else inr(0)} pending. Total "
        f"receivable {inr(receivables_total)} across {len(pending_all)} unpaid invoices. Ageing: "
        + "; ".join(f"{k}: {inr(v)} ({bucket_counts[k]} invoices)" for k, v in buckets.items()) + ". "
        f"Largest debtors: " + "; ".join(f"{r['party']} {inr(r['pending'])} (overdue {inr(r['overdue'])})" for r in receivables_rows[:8]) + "."
    )
    docs.append(Document(id="analytics:receivables", text=text, kind="analytics", title="Receivables ageing – party-wise outstanding",
                         metadata={"total": receivables_total}))

    # -- e-commerce -------------------------------------------------------------
    if ecom:
        by_channel: dict[str, list[dict]] = defaultdict(list)
        for o in ecom:
            by_channel[o.get("orderSource") or "Online"].append(o)
        sku_counts: dict[str, int] = defaultdict(int)
        for o in ecom:
            for it in o.get("items") or []:
                sku_counts[it.get("skuName")] += int(it.get("uomQty") or it.get("order_Qty") or 0)
        returned = [o for o in ecom if (o.get("status") or "").lower().startswith("return")]
        text = (
            f"E-commerce channel summary for {company}: {len(ecom)} marketplace orders worth "
            f"{inr(sum(float(o.get('orderAmount') or 0) for o in ecom))}. By channel: "
            + "; ".join(f"{c} {len(rows)} orders {inr(sum(float(o.get('orderAmount') or 0) for o in rows))}" for c, rows in by_channel.items())
            + f". Return rate {len(returned) / len(ecom) * 100:.1f}%. Best-selling online SKUs: "
            + ", ".join(f"{k} ({v} units)" for k, v in sorted(sku_counts.items(), key=lambda kv: kv[1], reverse=True)[:5]) + "."
        )
        docs.append(Document(id="analytics:ecom", text=text, kind="analytics", title="E-commerce summary", metadata={}))

    # -- item catalogue summary --------------------------------------------------
    items = data.get("items", [])
    if items:
        by_cat: dict[str, int] = defaultdict(int)
        for i in items:
            by_cat[i.get("category") or "general"] += 1
        margins = sorted(
            ((i.get("product"), (float(i["mrp"]) - float(i["cost"])) / float(i["mrp"]) * 100)
             for i in items if i.get("mrp") and i.get("cost")), key=lambda kv: kv[1], reverse=True)
        text = (
            f"Item catalogue summary for {company}: {len(items)} SKUs. By category: "
            + ", ".join(f"{k} {v}" for k, v in by_cat.items()) + ". Highest margin items on MRP: "
            + ", ".join(f"{n} ({m:.0f}%)" for n, m in margins[:6]) + ". Lowest margin items: "
            + ", ".join(f"{n} ({m:.0f}%)" for n, m in margins[-4:]) + "."
        )
        docs.append(Document(id="analytics:items", text=text, kind="analytics", title="Item catalogue summary", metadata={}))

    # -- overall snapshot -------------------------------------------------------
    total_sales = sum(_amount(r) for r in sales)
    total_purchases = sum(_amount(r) for r in purchases)
    first_month = next(iter(sales_by_month), None)
    last_month = next(reversed(sales_by_month), None)
    this_month = month_key(today)
    this_month_sales = sum(_amount(r) for r in sales_by_month.get(this_month, []))
    last_full_month = [m for m in sales_by_month if m < this_month]
    lfm = last_full_month[-1] if last_full_month else None
    lfm_sales = sum(_amount(r) for r in sales_by_month.get(lfm, [])) if lfm else 0
    pfm = last_full_month[-2] if len(last_full_month) > 1 else None
    pfm_sales = sum(_amount(r) for r in sales_by_month.get(pfm, [])) if pfm else 0
    text = (
        f"Business snapshot for {company} (data synced from MargBooks, {month_label(first_month) if first_month else ''} to "
        f"{month_label(last_month) if last_month else ''}): total sales {inr(total_sales)} across {len(sales)} invoices; "
        f"total purchases {inr(total_purchases)} across {len(purchases)} bills; {len(customers)} active customers; "
        f"{len(suppliers)} suppliers; {len(items)} SKUs. Month to date ({month_label(this_month)}) sales {inr(this_month_sales)}; "
        f"last full month ({month_label(lfm) if lfm else 'n/a'}) sales {inr(lfm_sales)}. Receivables outstanding "
        f"{inr(receivables_total)}; payables outstanding {inr(payables_total)}. Top 3 customers overall: "
        + "; ".join(f"{n} {inr(sum(_amount(r) for r in rows))}" for n, rows in ranked_customers[:3] if n != "Cash Account") + "."
    )
    docs.append(Document(id="analytics:snapshot", text=text, kind="analytics", title="Business snapshot", metadata={}))

    kpis = {
        "total_sales": round(total_sales, 2),
        "total_purchases": round(total_purchases, 2),
        "receivables": round(receivables_total, 2),
        "payables": round(payables_total, 2),
        "invoices": len(sales),
        "customers": len([c for c in customers if c != "Cash Account"]),
        "suppliers": len(suppliers),
        "items": len(items),
        "mtd_sales": round(this_month_sales, 2),
        "last_month_sales": round(lfm_sales, 2),
        "last_month_label": month_label(lfm) if lfm else None,
        "prev_month_sales": round(pfm_sales, 2),
        "prev_month_label": month_label(pfm) if pfm else None,
        "this_month_label": month_label(this_month),
        "monthly": monthly_series[-12:],
        "top_customers": [{"party": n, "total": round(sum(_amount(r) for r in rows), 2)} for n, rows in ranked_customers[:6] if n != "Cash Account"][:5],
        "receivables_rows": receivables_rows[:6],
        "ageing": [{"bucket": k, "amount": round(v, 2), "invoices": bucket_counts[k]} for k, v in buckets.items()],
    }
    return docs, kpis


def build_documents(data: dict[str, list[dict]], company: str, today: date | None = None) -> tuple[list[Document], dict]:
    today = today or date.today()
    docs: list[Document] = []
    for kind, dataset in (
        ("sale_bill", "sale_bills"), ("sale_order", "sale_orders"), ("sale_challan", "sale_challans"),
        ("purchase_bill", "purchase_bills"), ("purchase_order", "purchase_orders"),
        ("purchase_challan", "purchase_challans"), ("purchase_return", "purchase_returns"),
    ):
        for rec in data.get(dataset, []) or []:
            docs.append(bill_document(rec, kind, company))
    for rec in data.get("ledgers", []) or []:
        docs.append(ledger_document(rec))
    for rec in data.get("items", []) or []:
        docs.append(item_document(rec))
    for rec in data.get("ecom_orders", []) or []:
        docs.append(ecom_order_document(rec))
    analytics, kpis = analytics_documents(data, company, today)
    # Analytics first so ties in retrieval favour the aggregated view.
    return analytics + docs, kpis
