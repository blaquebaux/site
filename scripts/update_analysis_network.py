#!/usr/bin/env python3
"""Refresh conservative SEC intelligence for the ANALYSIS page.

Apple retains its separately reviewed filing analysis. The other configured
issuers receive an automated SEC filing/XBRL snapshot. Automated records do not
infer counterparties, relationships, consequences, or sleeve assignments.
"""
import argparse
import datetime as dt
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis" / "public-source-network.json"
HEADERS = {"User-Agent": "BLAQUE BAUX research contact ceo@carterwarrens.com"}
ISSUERS = {
    "AAPL": "0000320193", "MSFT": "0000789019", "NVDA": "0001045810",
    "GOOGL": "0001652044", "AMZN": "0001018724", "TSLA": "0001318605",
    "SPCX": "0001181412",
}
FACTS = (
    ("Revenue", ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues")),
    ("Net income", ("NetIncomeLoss",)),
    ("Operating cash flow", ("NetCashProvidedByUsedInOperatingActivities",)),
    ("Share repurchases", ("PaymentsForRepurchaseOfCommonStock",)),
    ("Cash and equivalents", ("CashAndCashEquivalentsAtCarryingValue",)),
)


def fetch_json(url):
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def latest_periodic(payload):
    recent = payload["filings"]["recent"]
    keys = ("form", "filingDate", "reportDate", "accessionNumber", "primaryDocument")
    for values in zip(*(recent[key] for key in keys)):
        row = dict(zip(keys, values))
        if row["form"] in {"10-Q", "10-K"}:
            return row
    raise ValueError("No recent 10-Q or 10-K found")


def filing_url(cik, filing):
    accession = filing["accessionNumber"].replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{filing['primaryDocument']}"


def choose_fact(companyfacts, concepts, accession):
    us_gaap = companyfacts.get("facts", {}).get("us-gaap", {})
    for concept in concepts:
        fact = us_gaap.get(concept)
        if not fact:
            continue
        candidates = []
        for unit, rows in fact.get("units", {}).items():
            if unit not in {"USD", "shares"}:
                continue
            for row in rows:
                if row.get("accn") == accession and row.get("form") in {"10-Q", "10-K"}:
                    candidates.append((concept, unit, row))
        if candidates:
            def rank(item):
                row = item[2]
                if row.get("start"):
                    span = (dt.date.fromisoformat(row["end"]) - dt.date.fromisoformat(row["start"])).days
                else:
                    span = -1
                return (row.get("filed", ""), row.get("end", ""), -span)
            return max(candidates, key=rank)
    return None


def compact_value(value, unit):
    if unit == "shares":
        return f"{value / 1_000_000:.1f}M shares"
    magnitude = abs(value)
    sign = "-" if value < 0 else ""
    if magnitude >= 1_000_000_000:
        return f"{sign}${magnitude / 1_000_000_000:.1f}B"
    if magnitude >= 1_000_000:
        return f"{sign}${magnitude / 1_000_000:.1f}M"
    return f"{sign}${magnitude:,.0f}"


def observation(label, selected):
    concept, unit, row = selected
    period = row["end"] if not row.get("start") else f"{row['start']} to {row['end']}"
    interpretations = {
        "Revenue": "Neutral observation. Revenue scale or change requires segment, margin, demand and comparability context.",
        "Net income": "Neutral observation. Net income requires reconciliation to operating drivers, cash flow and non-recurring items.",
        "Operating cash flow": "Neutral observation. Cash generation should be read with working capital, capital spending and period length.",
        "Share repurchases": "Neutral observation. Repurchases may be constructive or adverse depending on valuation, funding, liquidity and alternatives.",
        "Cash and equivalents": "Neutral observation. Cash is a liquidity input, not a standalone conclusion about resilience or excess capital.",
    }
    return {
        "id": f"{row['accn'].lower()}-{concept.lower()}",
        "type": "structured_financial_fact",
        "classification": "SEC XBRL structured fact; automated extraction",
        "label": label,
        "value": compact_value(row["val"], unit),
        "period": period,
        "detail": f"Issuer-tagged us-gaap:{concept}; fiscal period {row.get('fp', 'not stated')}. No adjustment or cross-company normalization applied.",
        "interpretation": interpretations[label],
        "source_locator": f"SEC Companyfacts / us-gaap:{concept}",
    }


def build_structured_entity(ticker, cik, submissions, companyfacts):
    filing = latest_periodic(submissions)
    accession = filing["accessionNumber"]
    observations = []
    for label, concepts in FACTS:
        selected = choose_fact(companyfacts, concepts, accession)
        if selected:
            observations.append(observation(label, selected))
    return {
        "name": submissions.get("name") or companyfacts.get("entityName") or ticker,
        "cik": cik,
        "source_period": filing["reportDate"], "source_filed": filing["filingDate"],
        "source_form": filing["form"], "source_accession": accession,
        "source_url": filing_url(cik, filing),
        "latest_detected": {"form": filing["form"], "filing_date": filing["filingDate"], "accession": accession},
        "review_state": "structured_only",
        "review_note": "Automated SEC filing metadata and issuer-tagged XBRL facts. Narrative context and relationships have not been reviewed.",
        "observations": observations, "relationships": [], "hypotheses": [],
        "eligible_sleeves": [], "assigned_sleeve": None,
    }


def validate(feed):
    assert feed["dataset_state"] in {"CURRENT_PUBLIC_SOURCE", "REVIEW_REQUIRED"}
    assert set(ISSUERS).issubset(feed["entities"])
    for ticker in ISSUERS:
        entity = feed["entities"][ticker]
        assert entity["source_url"].startswith("https://www.sec.gov/")
        assert entity["review_state"] in {"current", "review_required", "structured_only"}
        assert entity["observations"]
        for item in entity["observations"]:
            assert item["classification"] and item["source_locator"] and item["period"]
        if entity["review_state"] == "structured_only":
            assert entity["relationships"] == [] and entity["hypotheses"] == []
            assert entity["assigned_sleeve"] is None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate only; do not call SEC")
    args = parser.parse_args()
    feed = json.loads(DATA.read_text())
    if args.check:
        validate(feed)
        print("public-source network contract valid")
        return
    review_required = False
    for ticker, cik in ISSUERS.items():
        submissions = fetch_json(f"https://data.sec.gov/submissions/CIK{cik}.json")
        filing = latest_periodic(submissions)
        if ticker == "AAPL" and ticker in feed["entities"]:
            entity = feed["entities"][ticker]
            entity["latest_detected"] = {"form": filing["form"], "filing_date": filing["filingDate"], "accession": filing["accessionNumber"]}
            if filing["accessionNumber"] != entity["source_accession"]:
                entity["review_state"] = "review_required"
                review_required = True
            else:
                entity["review_state"] = "current"
            continue
        companyfacts = fetch_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")
        feed["entities"][ticker] = build_structured_entity(ticker, cik, submissions, companyfacts)
    feed["dataset_state"] = "REVIEW_REQUIRED" if review_required else "CURRENT_PUBLIC_SOURCE"
    feed["refreshed_at"] = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    feed["coverage_note"] = "SEC XBRL supplies issuer-tagged financial facts, not named supply-chain relationships. Relationship maps remain empty until narrative disclosures or counterparty filings are reviewed."
    validate(feed)
    DATA.write_text(json.dumps(feed, indent=2) + "\n")
    print(f"SEC intelligence refreshed for {len(ISSUERS)} issuers")


if __name__ == "__main__":
    main()
