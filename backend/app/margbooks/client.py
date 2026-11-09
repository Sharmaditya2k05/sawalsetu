"""Thin client for the MargBooks Open API.

Endpoint map (from https://openapiweb.margbooks.com, API v1, May 2023):

  Production  https://openapi.margbooks.com/
  Sandbox     https://uatopenapi.margbooks.com/

  Every call is an HTTP POST with a JSON body and two headers issued at signup
  (POST identity/v1/auth/signup returns {"apiKey": ..., "partnerId": ...}):

      MB Key:      <api key>
      Partner Id:  <partner id>

  Responses share one envelope:
      {"data": [...], "statusCode": 200, "errorCode": 0, "message": "Success", "detailedMessage": null}
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any

import httpx

log = logging.getLogger(__name__)

ENDPOINTS: dict[str, str] = {
    # Sales
    "sale_bills": "masters/v1/bills/salebills",
    "sale_orders": "masters/v1/bills/saleOrders",
    "sale_challans": "masters/v1/bills/salechallans",
    # Purchase
    "purchase_bills": "masters/v1/bills/purchasebills",
    "purchase_orders": "masters/v1/bills/PurchaseOrders",
    "purchase_challans": "masters/v1/bills/PurchaseChallans",
    "purchase_returns": "masters/v1/bills/prList",
    # Masters
    "ledgers": "masters/v1/Account/listledger",
    "ledger": "masters/v1/Account/getledger",
    "account_groups": "masters/v1/account/grouplist",
    "items": "masters/v1/products/list",
    "stores": "masters/v1/store/list",
    "item_companies": "masters/v1/itemcompany/list",
    "hsn": "masters/v1/hsn/list",
    "units": "masters/v1/inventory/allUnits",
    "sale_types": "masters/v1/taxtypes/saletypes",
    # E-commerce orders (Amazon / Flipkart / Meesho channels)
    "ecom_orders": "orders/v1/Orders/list",
}

DATE_RANGE_DATASETS = (
    "sale_bills",
    "sale_orders",
    "sale_challans",
    "purchase_bills",
    "purchase_orders",
    "purchase_challans",
    "purchase_returns",
)

SIMPLE_DATASETS = ("stores", "hsn", "units", "account_groups", "item_companies", "sale_types")


class MargBooksError(RuntimeError):
    pass


class MargBooksClient:
    def __init__(self, base_url: str, mb_key: str, partner_id: str, timeout: float = 60.0):
        if not mb_key or not partner_id:
            raise MargBooksError("MARGBOOKS_MB_KEY and MARGBOOKS_PARTNER_ID are required in live mode")
        self._client = httpx.Client(
            base_url=base_url.rstrip("/") + "/",
            headers={
                "accept": "application/json",
                "content-type": "application/json",
                "MB Key": mb_key,
                "Partner Id": partner_id,
            },
            timeout=timeout,
        )

    # -- low level -----------------------------------------------------------------
    def post(self, dataset: str, body: dict[str, Any] | None = None) -> Any:
        path = ENDPOINTS[dataset]
        response = self._client.post(path, json=body or {})
        if response.status_code == 401:
            raise MargBooksError("MargBooks rejected the credentials (401). Check MB Key / Partner Id.")
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict) and "data" in payload:
            if payload.get("errorCode") not in (0, None):
                raise MargBooksError(
                    f"{dataset}: errorCode={payload.get('errorCode')} {payload.get('message')} "
                    f"{payload.get('detailedMessage') or ''}".strip()
                )
            return payload["data"]
        return payload

    # -- datasets -------------------------------------------------------------------
    @staticmethod
    def _fmt(d: date) -> str:
        return d.strftime("%Y-%m-%d")

    def list_by_date(self, dataset: str, start: date, end: date, ledger_id: int | None = None) -> list[dict]:
        body: dict[str, Any] = {"fromDate": self._fmt(start), "toDate": self._fmt(end)}
        if ledger_id:
            body["ledgerId"] = ledger_id
        return list(self.post(dataset, body) or [])

    def list_items(self, page_size: int = 500) -> list[dict]:
        items: list[dict] = []
        page = 1
        while True:
            chunk = self.post("items", {"pageNumber": page, "pageSize": page_size}) or []
            items.extend(chunk)
            if len(chunk) < page_size:
                break
            page += 1
        return items

    def list_ledgers(self) -> list[dict]:
        return list(self.post("ledgers", {}) or [])

    def list_simple(self, dataset: str) -> list[dict]:
        data = self.post(dataset, {})
        return list(data or []) if isinstance(data, list) else []

    def list_ecom_orders(self, start: date, end: date, status: str = "closed") -> list[dict]:
        body = {
            "fromDate": start.strftime("%Y/%m/%d"),
            "toDate": end.strftime("%Y/%m/%d"),
            "filterBy": 2,
            "FullfillMentLocation": "",
            "status": status,
        }
        try:
            return list(self.post("ecom_orders", body) or [])
        except (httpx.HTTPError, MargBooksError) as exc:  # optional module, tolerate absence
            log.warning("ecom orders unavailable: %s", exc)
            return []

    def fetch_everything(self, start: date, end: date) -> dict[str, list[dict]]:
        out: dict[str, list[dict]] = {}
        for ds in DATE_RANGE_DATASETS:
            try:
                out[ds] = self.list_by_date(ds, start, end)
            except (httpx.HTTPError, MargBooksError) as exc:
                log.warning("%s failed: %s", ds, exc)
                out[ds] = []
        out["ledgers"] = self.list_ledgers()
        out["items"] = self.list_items()
        for ds in SIMPLE_DATASETS:
            try:
                out[ds] = self.list_simple(ds)
            except (httpx.HTTPError, MargBooksError) as exc:
                log.warning("%s failed: %s", ds, exc)
                out[ds] = []
        out["ecom_orders"] = self.list_ecom_orders(start, end)
        return out
