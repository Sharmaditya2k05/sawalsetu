"""Deterministic demo dataset shaped exactly like the MargBooks Open API responses.

Used when MARGBOOKS_MODE=demo so the whole pipeline (sync -> index -> answer) can be
exercised without live credentials. Field names mirror the API docs so the rest of the
code does not know whether it is looking at demo or live data.

The business modelled is a pharma + FMCG distributor in Jaipur, which is the segment
MargBooks is most used in.
"""
from __future__ import annotations

import random
from datetime import date, datetime, timedelta

CUSTOMERS = [
    ("Apollo Pharmacy – Malviya Nagar", "Jaipur", 21, 30),
    ("Wellness Forever – C Scheme", "Jaipur", 21, 30),
    ("MedPlus – Vaishali Nagar", "Jaipur", 21, 45),
    ("Shri Ram Medical Store", "Jaipur", 21, 15),
    ("Jeevan Medicos", "Ajmer", 21, 30),
    ("Sanjeevani Chemists", "Kota", 21, 30),
    ("Raj Medical Hall", "Udaipur", 21, 45),
    ("New Life Pharmacy", "Alwar", 21, 15),
    ("Krishna Medical & General Store", "Sikar", 21, 30),
    ("Dhanvantari Drug House", "Bikaner", 21, 60),
    ("Mahaveer Medicals", "Jodhpur", 21, 30),
    ("Noble Chemist", "Jaipur", 21, 7),
    ("City Care Pharmacy", "Jaipur", 21, 30),
    ("Gupta Provision Store", "Jaipur", 21, 7),
    ("Balaji Super Mart", "Jaipur", 21, 15),
    ("Reliance Smart Point – Tonk Road", "Jaipur", 21, 30),
    ("Ganpati Kirana", "Dausa", 21, 7),
    ("Rathore General Store", "Jodhpur", 21, 15),
    ("Vardhman Medicose", "Bhilwara", 21, 45),
    ("Nirmal Pharma Retail", "Delhi", 7, 30),
    ("Om Sai Chemist", "Gurugram", 6, 30),
    ("Lotus Pharmacy", "Jaipur", 21, 30),
    ("Shakti Medical Agency", "Ahmedabad", 24, 45),
    ("Arogya Wellness Store", "Jaipur", 21, 15),
]

SUPPLIERS = [
    ("Sun Pharmaceutical Industries Ltd", "Mumbai", 27),
    ("Cipla Ltd", "Mumbai", 27),
    ("Dr. Reddy's Laboratories", "Hyderabad", 36),
    ("Mankind Pharma", "Delhi", 7),
    ("Alkem Laboratories", "Mumbai", 27),
    ("Zydus Lifesciences", "Ahmedabad", 24),
    ("Himalaya Wellness", "Bengaluru", 29),
    ("Dabur India Ltd", "Ghaziabad", 9),
    ("Hindustan Unilever – Distributor Supply", "Mumbai", 27),
    ("Patanjali Ayurved", "Haridwar", 5),
    ("Abbott Healthcare", "Mumbai", 27),
    ("Torrent Pharmaceuticals", "Ahmedabad", 24),
]

ITEMS = [
    # (product, company, unit, mrp, cost, hsn, type)
    ("Dolo 650 Tablet 15s", "Micro Labs", "STRIP", 33.6, 25.2, 3004, "pharma"),
    ("Crocin Advance 500mg 15s", "GSK", "STRIP", 31.5, 24.0, 3004, "pharma"),
    ("Azithral 500 Tablet 5s", "Alembic", "STRIP", 119.5, 88.0, 3004, "pharma"),
    ("Augmentin 625 Duo 10s", "GSK", "STRIP", 223.0, 170.0, 3004, "pharma"),
    ("Pan 40 Tablet 15s", "Alkem", "STRIP", 170.0, 125.0, 3004, "pharma"),
    ("Pan-D Capsule 15s", "Alkem", "STRIP", 212.0, 158.0, 3004, "pharma"),
    ("Telma 40 Tablet 15s", "Glenmark", "STRIP", 196.0, 148.0, 3004, "pharma"),
    ("Amlodipine 5mg 10s", "Cipla", "STRIP", 28.0, 19.0, 3004, "pharma"),
    ("Metformin 500mg 20s", "Sun Pharma", "STRIP", 32.0, 21.0, 3004, "pharma"),
    ("Glycomet GP 2 15s", "USV", "STRIP", 145.0, 108.0, 3004, "pharma"),
    ("Atorva 10 Tablet 15s", "Zydus", "STRIP", 118.0, 86.0, 3004, "pharma"),
    ("Ecosprin 75 14s", "USV", "STRIP", 11.5, 8.2, 3004, "pharma"),
    ("Shelcal 500 15s", "Torrent", "STRIP", 112.0, 82.0, 3004, "pharma"),
    ("Becosules Capsule 20s", "Pfizer", "STRIP", 46.0, 34.0, 3004, "pharma"),
    ("Zincovit Tablet 15s", "Apex", "STRIP", 105.0, 76.0, 3004, "pharma"),
    ("Limcee 500 Chewable 15s", "Abbott", "STRIP", 25.4, 18.0, 3004, "pharma"),
    ("Cetirizine 10mg 10s", "Cipla", "STRIP", 19.0, 12.5, 3004, "pharma"),
    ("Allegra 120 10s", "Sanofi", "STRIP", 218.0, 165.0, 3004, "pharma"),
    ("Montek LC 10s", "Sun Pharma", "STRIP", 219.0, 162.0, 3004, "pharma"),
    ("Ascoril LS Syrup 100ml", "Glenmark", "BOTTLE", 118.0, 86.0, 3004, "pharma"),
    ("Benadryl Cough Syrup 150ml", "J&J", "BOTTLE", 131.0, 98.0, 3004, "pharma"),
    ("Digene Gel 200ml", "Abbott", "BOTTLE", 139.0, 104.0, 3004, "pharma"),
    ("Gelusil MPS 200ml", "Pfizer", "BOTTLE", 129.0, 96.0, 3004, "pharma"),
    ("ORS Electral Sachet 21g", "FDC", "SACHET", 21.0, 15.0, 3004, "pharma"),
    ("Volini Spray 100g", "Sun Pharma", "PCS", 299.0, 225.0, 3004, "pharma"),
    ("Moov Cream 50g", "Reckitt", "PCS", 160.0, 118.0, 3004, "pharma"),
    ("Betadine Ointment 20g", "Win-Medicare", "PCS", 125.0, 92.0, 3004, "pharma"),
    ("Soframycin Cream 30g", "Sanofi", "PCS", 54.0, 39.0, 3004, "pharma"),
    ("Insulin Human Mixtard 30/70 10ml", "Novo Nordisk", "VIAL", 169.0, 140.0, 3004, "pharma"),
    ("Thyronorm 50mcg 120s", "Abbott", "BOTTLE", 188.0, 142.0, 3004, "pharma"),
    ("Dettol Antiseptic 550ml", "Reckitt", "BOTTLE", 215.0, 168.0, 3808, "fmcg"),
    ("Savlon Handwash 200ml", "ITC", "BOTTLE", 99.0, 74.0, 3401, "fmcg"),
    ("Lifebuoy Soap 125g x4", "HUL", "PACK", 136.0, 108.0, 3401, "fmcg"),
    ("Dove Shampoo 340ml", "HUL", "BOTTLE", 310.0, 242.0, 3305, "fmcg"),
    ("Colgate Strong Teeth 200g", "Colgate", "PCS", 115.0, 90.0, 3306, "fmcg"),
    ("Sensodyne Repair 70g", "GSK", "PCS", 180.0, 140.0, 3306, "fmcg"),
    ("Himalaya Neem Face Wash 150ml", "Himalaya", "BOTTLE", 185.0, 139.0, 3304, "fmcg"),
    ("Dabur Chyawanprash 1kg", "Dabur", "PCS", 425.0, 330.0, 3004, "fmcg"),
    ("Dabur Honey 500g", "Dabur", "PCS", 235.0, 180.0, 409, "fmcg"),
    ("Patanjali Aloe Vera Gel 150ml", "Patanjali", "PCS", 85.0, 62.0, 3304, "fmcg"),
    ("Horlicks Classic 1kg", "HUL", "PCS", 515.0, 420.0, 1901, "fmcg"),
    ("Bournvita 1kg", "Mondelez", "PCS", 460.0, 372.0, 1806, "fmcg"),
    ("Pampers Pants M 56s", "P&G", "PACK", 899.0, 720.0, 9619, "fmcg"),
    ("Whisper Ultra XL 30s", "P&G", "PACK", 295.0, 232.0, 9619, "fmcg"),
    ("Accu-Chek Active Strips 50s", "Roche", "BOX", 1200.0, 980.0, 3822, "device"),
    ("Dr. Morepen BP Monitor BP-15", "Morepen", "PCS", 2199.0, 1650.0, 9018, "device"),
    ("Omron HEM-7120 BP Monitor", "Omron", "PCS", 2490.0, 1950.0, 9018, "device"),
    ("Digital Thermometer MT-101", "Dr Trust", "PCS", 299.0, 190.0, 9025, "device"),
    ("N95 Mask 5s", "Venus", "PACK", 199.0, 130.0, 6307, "device"),
    ("Surgical Gloves Latex 100s", "Kanam", "BOX", 650.0, 480.0, 4015, "device"),
]

STORES = [
    {"uniqueId": 9001, "name": "Main Godown – Sitapura", "city": "Jaipur"},
    {"uniqueId": 9002, "name": "Retail Counter – Tonk Road", "city": "Jaipur"},
]

ECOM_SKUS = ["Dabur Chyawanprash 1kg", "Himalaya Neem Face Wash 150ml", "Dr. Morepen BP Monitor BP-15",
             "Accu-Chek Active Strips 50s", "N95 Mask 5s", "Dove Shampoo 340ml", "Horlicks Classic 1kg"]


def _iso(d: date) -> str:
    return datetime(d.year, d.month, d.day).strftime("%Y-%m-%dT%H:%M:%S")


def _season(month: int) -> float:
    # Monsoon/winter demand lift for pharma, festive lift for FMCG in Oct/Nov.
    return {1: 1.05, 2: 0.95, 3: 1.0, 4: 0.9, 5: 0.92, 6: 0.98, 7: 1.12, 8: 1.18, 9: 1.1,
            10: 1.22, 11: 1.15, 12: 1.04}[month]


def generate(start: date, end: date, seed: int = 42) -> dict[str, list[dict]]:
    rng = random.Random(seed)
    today = end

    ledgers: list[dict] = []
    ledger_ids: dict[str, int] = {}
    next_id = 423639000000
    for name, city, state_id, credit_days in CUSTOMERS:
        next_id += rng.randint(1000, 9000)
        ledger_ids[name] = next_id
        ledgers.append({
            "uniqueId": next_id, "name": name, "alias": name.split(" –")[0], "accountGroupId": 101,
            "gstApplicable": 1, "email": None, "address1": f"{rng.randint(1, 99)}, Market Road",
            "address2": city, "address3": "", "countryId": 1, "stateId": state_id, "city": city,
            "postalCode": None, "openingBalance": round(rng.uniform(0, 45000), 2), "ledgerType": 1,
            "pan": None, "creditLimit": rng.choice([50000, 100000, 150000, 250000]),
            "creditLimitDays": credit_days, "ledgerKind": "customer",
        })
    for name, city, state_id in SUPPLIERS:
        next_id += rng.randint(1000, 9000)
        ledger_ids[name] = next_id
        ledgers.append({
            "uniqueId": next_id, "name": name, "alias": name.split(" ")[0], "accountGroupId": 201,
            "gstApplicable": 1, "email": None, "address1": "Corporate Office", "address2": city,
            "address3": "", "countryId": 1, "stateId": state_id, "city": city, "postalCode": None,
            "openingBalance": 0, "ledgerType": 2, "pan": None, "creditLimit": 0,
            "creditLimitDays": rng.choice([30, 45, 60]), "ledgerKind": "supplier",
        })
    next_id += 777
    ledger_ids["Cash Account"] = next_id
    ledgers.append({"uniqueId": next_id, "name": "Cash Account", "alias": "Cash", "accountGroupId": 1,
                    "gstApplicable": 0, "city": "Jaipur", "stateId": 21, "openingBalance": 25000,
                    "ledgerType": 0, "creditLimit": 0, "creditLimitDays": 0, "ledgerKind": "cash"})

    items: list[dict] = []
    for i, (product, company, unit, mrp, cost, hsn, kind) in enumerate(ITEMS):
        items.append({
            "uniqueId": 423639700000 + i * 13, "itemCode": f"SKU{1001 + i}", "unit": unit, "packing": "",
            "mrp": mrp, "cost": cost, "hsn": hsn, "product": product, "printName": product,
            "companyName": company, "itemType": 1, "category": kind,
            "minimumQuantity": rng.choice([10, 20, 30, 50]), "reorderQuantity": rng.choice([50, 100, 200]),
            "reorderDays": rng.choice([7, 15]), "status": 0, "narcotic": 0,
            "scheduleH": 1 if kind == "pharma" and rng.random() < 0.5 else 0,
        })

    # Weighted customer popularity so the data has clear "top customers".
    customer_weights = [rng.uniform(0.4, 1.0) ** 2 for _ in CUSTOMERS]
    customer_weights[0] *= 3.2  # Apollo
    customer_weights[1] *= 2.4  # Wellness Forever
    customer_weights[2] *= 2.0  # MedPlus
    customer_weights[15] *= 1.8  # Reliance Smart Point

    sale_bills: list[dict] = []
    sale_orders: list[dict] = []
    sale_challans: list[dict] = []
    bill_no = 1000
    d = start
    while d <= end:
        if d.weekday() != 6:  # closed on Sundays
            n_bills = max(1, int(rng.gauss(3.2 * _season(d.month), 1.1)))
            for _ in range(n_bills):
                idx = rng.choices(range(len(CUSTOMERS)), weights=customer_weights)[0]
                name, city, _state, credit_days = CUSTOMERS[idx]
                qty = rng.randint(12, 420)
                amount = round(qty * rng.uniform(42, 310) * (1.35 if idx in (0, 1, 2, 15) else 1.0), 2)
                discount = round(amount * rng.choice([0, 0, 0.02, 0.03, 0.05]), 2)
                age = (today - d).days
                if age > credit_days + 25:
                    status = "Paid" if rng.random() < 0.93 else "Pending"
                elif age > credit_days:
                    status = "Paid" if rng.random() < 0.62 else "Pending"
                else:
                    status = "Paid" if rng.random() < 0.28 else "Pending"
                bill_no += 1
                sale_bills.append({
                    "uniqueId": 1530000000000 + bill_no * 7, "ledgerName": name, "status": status,
                    "billDate": _iso(d), "deliveryDate": "0001-01-01T00:00:00", "ledgerId": ledger_ids[name],
                    "billNo": f"SB/{d.strftime('%y')}/{bill_no}", "customerMobileNo": None,
                    "doctorMobileNo": None, "storeId": rng.choice([9001, 9001, 9002]), "billTypeId": 1,
                    "billDiscountPer": round(discount / amount * 100, 2) if amount else 0,
                    "billDiscountAmount": discount, "totalQty": qty, "totalAmount": round(amount - discount, 2),
                    "totalDiscount": discount, "creditDays": credit_days, "remarks": None,
                })
            # Counter sales (cash) a few times a week
            if rng.random() < 0.55:
                bill_no += 1
                amt = round(rng.uniform(800, 9000), 2)
                sale_bills.append({
                    "uniqueId": 1530000000000 + bill_no * 7, "ledgerName": "Cash Account", "status": "Paid",
                    "billDate": _iso(d), "deliveryDate": "0001-01-01T00:00:00",
                    "ledgerId": ledger_ids["Cash Account"], "billNo": f"CS/{d.strftime('%y')}/{bill_no}",
                    "customerMobileNo": None, "doctorMobileNo": None, "storeId": 9002, "billTypeId": 2,
                    "billDiscountPer": 0, "billDiscountAmount": 0, "totalQty": rng.randint(3, 40),
                    "totalAmount": amt, "totalDiscount": 0, "creditDays": 0, "remarks": "Counter sale",
                })
            if rng.random() < 0.35:
                idx = rng.choices(range(len(CUSTOMERS)), weights=customer_weights)[0]
                name = CUSTOMERS[idx][0]
                qty = rng.randint(20, 300)
                sale_orders.append({
                    "uniqueId": 1540000000000 + len(sale_orders) * 11, "ledgerName": name,
                    "status": "Pending" if (today - d).days < 10 else "Closed", "billDate": _iso(d),
                    "deliveryDate": _iso(d + timedelta(days=rng.randint(1, 4))), "ledgerId": ledger_ids[name],
                    "billNo": f"SO/{d.strftime('%y')}/{len(sale_orders) + 1}", "storeId": 9001, "billTypeId": 1,
                    "totalQty": qty, "totalAmount": round(qty * rng.uniform(40, 250), 2), "totalDiscount": 0,
                    "creditDays": CUSTOMERS[idx][3], "remarks": None,
                })
            if rng.random() < 0.2:
                idx = rng.choices(range(len(CUSTOMERS)), weights=customer_weights)[0]
                name = CUSTOMERS[idx][0]
                sale_challans.append({
                    "uniqueId": 1550000000000 + len(sale_challans) * 3, "ledgerName": name, "status": "Delivered",
                    "billDate": _iso(d), "deliveryDate": _iso(d), "ledgerId": ledger_ids[name],
                    "billNo": f"DC/{d.strftime('%y')}/{len(sale_challans) + 1}", "storeId": 9001,
                    "totalQty": rng.randint(10, 200), "totalAmount": 0, "totalDiscount": 0, "remarks": None,
                })
        d += timedelta(days=1)

    purchase_bills: list[dict] = []
    purchase_orders: list[dict] = []
    purchase_returns: list[dict] = []
    supplier_weights = [1.0] * len(SUPPLIERS)
    supplier_weights[0] = 2.4  # Sun Pharma
    supplier_weights[1] = 2.0  # Cipla
    supplier_weights[3] = 1.7  # Mankind
    d = start
    pno = 500
    while d <= end:
        if rng.random() < 0.42:
            idx = rng.choices(range(len(SUPPLIERS)), weights=supplier_weights)[0]
            name, city, _state = SUPPLIERS[idx]
            qty = rng.randint(200, 3000)
            amount = round(qty * rng.uniform(35, 180), 2)
            age = (today - d).days
            status = "Paid" if age > 50 and rng.random() < 0.95 else ("Paid" if rng.random() < 0.4 else "Pending")
            pno += 1
            purchase_bills.append({
                "uniqueId": 1372000000000 + pno * 5, "ledgerName": name, "status": status, "billDate": _iso(d),
                "deliveryDate": "0001-01-01T00:00:00", "ledgerId": ledger_ids[name],
                "billNo": f"PB/{d.strftime('%y')}/{pno}", "storeId": 9001, "billTypeId": 1, "billDiscountPer": 0,
                "billDiscountAmount": 0, "totalQty": qty, "totalAmount": amount,
                "totalDiscount": round(amount * rng.choice([0, 0, 0.01, 0.02]), 2), "remarks": None,
            })
            if rng.random() < 0.3:
                purchase_orders.append({
                    "uniqueId": 1373000000000 + len(purchase_orders) * 9, "ledgerName": name,
                    "status": "Pending" if age < 14 else "Closed", "billDate": _iso(d - timedelta(days=rng.randint(3, 9))),
                    "deliveryDate": _iso(d), "ledgerId": ledger_ids[name],
                    "billNo": f"PO/{d.strftime('%y')}/{len(purchase_orders) + 1}", "storeId": 9001,
                    "totalQty": qty, "totalTaxAmount": round(amount * 0.12, 2), "totalAmount": round(amount * 1.12, 2),
                    "totalItemsAmount": amount, "totalDiscount": 0, "remarks": None,
                })
            if rng.random() < 0.08:
                ret_amt = round(amount * rng.uniform(0.03, 0.12), 2)
                purchase_returns.append({
                    "uniqueId": 1374000000000 + len(purchase_returns) * 17, "ledgerName": name, "status": "Closed",
                    "billDate": _iso(d + timedelta(days=rng.randint(5, 20))), "ledgerId": ledger_ids[name],
                    "billNo": f"PR/{d.strftime('%y')}/{len(purchase_returns) + 1}", "storeId": 9001,
                    "totalQty": rng.randint(5, 80), "totalAmount": ret_amt, "totalDiscount": 0,
                    "remarks": rng.choice(["Near expiry", "Damaged in transit", "Excess supply", "Batch recall"]),
                })
        d += timedelta(days=1)

    ecom_orders: list[dict] = []
    d = max(start, end - timedelta(days=120))
    while d <= end:
        for _ in range(rng.randint(0, 3)):
            sku = rng.choice(ECOM_SKUS)
            item = next(i for i in items if i["product"] == sku)
            qty = rng.randint(1, 4)
            channel = rng.choice(["Amazon", "Amazon", "Flipkart", "Meesho"])
            ecom_orders.append({
                "orderNo": f"{channel[:2].upper()}-{d.strftime('%y%m%d')}-{rng.randint(100, 999)}",
                "orderId": f"{rng.randint(10**8, 10**9 - 1)}", "orderLocation": "SITAPURA", "externalOrderNo": None,
                "paymentMethod": rng.choice(["Prepaid", "Prepaid", "COD"]),
                "status": rng.choice(["Shipped complete", "Shipped complete", "Delivered", "Returned"]),
                "orderDate": d.strftime("%d/%m/%Y %H:%M:%S"), "orderAmount": round(item["mrp"] * qty * 0.92, 2),
                "orderCurrency": "INR", "customerName": rng.choice(["Rohit S.", "Priya M.", "Anjali K.", "Vikram R.", "Neha G."]),
                "orderType": "SO", "orderSource": channel, "items": [{
                    "lineNo": 1, "sku": item["itemCode"], "skuName": sku, "uom": "Each", "uomQty": qty,
                    "order_Qty": qty, "shipped_qty": qty, "unit_price": round(item["mrp"] * 0.92, 2),
                }],
            })
        d += timedelta(days=1)

    return {
        "sale_bills": sale_bills,
        "sale_orders": sale_orders,
        "sale_challans": sale_challans,
        "purchase_bills": purchase_bills,
        "purchase_orders": purchase_orders,
        "purchase_challans": [],
        "purchase_returns": purchase_returns,
        "ledgers": ledgers,
        "items": items,
        "stores": STORES,
        "hsn": sorted({str(i["hsn"]) for i in items}),
        "units": sorted({i["unit"] for i in items}),
        "account_groups": [{"uniqueId": 101, "name": "Sundry Debtors"}, {"uniqueId": 201, "name": "Sundry Creditors"},
                           {"uniqueId": 1, "name": "Cash-in-Hand"}],
        "item_companies": sorted({i["companyName"] for i in items}),
        "sale_types": [{"uniqueId": 1, "name": "GST Sale 12%"}, {"uniqueId": 2, "name": "GST Sale 18%"}],
        "ecom_orders": ecom_orders,
    }
