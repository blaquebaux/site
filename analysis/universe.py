"""Discover the broad ANALYSIS equity universe without assigning research views.

The SEC ticker file supplies issuer identity and CIK. Alpaca's active US-equity
asset directory supplies the market symbols the existing price pipeline can
request. Only the intersection is auto-added. Curated records in build_data.py
always win and retain their researched metadata.
"""
import json
import urllib.request


SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
ALPACA_ASSETS_URL = "https://api.alpaca.markets/v2/assets?status=active&asset_class=us_equity"
SUPPORTED_EXCHANGES = {"AMEX", "ARCA", "BATS", "NASDAQ", "NYSE"}


def canonical_ticker(value):
    """Use the page's dot convention for class shares (BRK-B -> BRK.B)."""
    return value.strip().upper().replace("-", ".")


def request_json(url, headers):
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.load(response)


def discover_sec_alpaca_universe(alpaca_headers):
    sec = request_json(
        SEC_TICKERS_URL,
        {"User-Agent": "BLAQUE BAUX research contact ceo@carterwarrens.com"},
    )
    assets = request_json(ALPACA_ASSETS_URL, alpaca_headers)
    issuers = {
        canonical_ticker(row["ticker"]): {
            "name": row["title"].strip(),
            "cik": str(row["cik_str"]).zfill(10),
        }
        for row in sec.values()
        if row.get("ticker") and row.get("title") and row.get("cik_str") is not None
    }
    discovered = {}
    for asset in assets:
        ticker = canonical_ticker(asset.get("symbol", ""))
        issuer = issuers.get(ticker)
        if (
            not ticker
            or not issuer
            or asset.get("status") != "active"
            or not asset.get("tradable")
            or asset.get("exchange") not in SUPPORTED_EXCHANGES
        ):
            continue
        discovered[ticker] = {
            **issuer,
            "exchange": asset["exchange"],
            "provider_symbol": asset["symbol"],
        }
    return discovered
