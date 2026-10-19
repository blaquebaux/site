#!/usr/bin/env python3
"""Check SEC submissions for newer AAPL 10-Q/10-K filings.

This monitor never extracts or invents relationships automatically. It marks the
published record for review when a newer filing appears, preserving the last
reviewed facts until a human updates their locators and interpretations.
"""
import argparse
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis" / "public-source-network.json"
SEC_SUBMISSIONS = "https://data.sec.gov/submissions/CIK0000320193.json"
HEADERS = {"User-Agent": "BLAQUE BAUX research contact ceo@carterwarrens.com"}


def latest_periodic(payload):
    recent = payload["filings"]["recent"]
    rows = zip(recent["form"], recent["filingDate"], recent["accessionNumber"])
    return next({"form": form, "filing_date": date, "accession": accession}
                for form, date, accession in rows if form in {"10-Q", "10-K"})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate only; do not call SEC")
    args = parser.parse_args()
    feed = json.loads(DATA.read_text())
    apple = feed["entities"]["AAPL"]
    if args.check:
        assert feed["dataset_state"] in {"CURRENT_PUBLIC_SOURCE", "REVIEW_REQUIRED"}
        assert apple["source_url"].startswith("https://www.sec.gov/")
        assert apple["review_state"] in {"current", "review_required"}
        assert apple["relationships"] and apple["observations"]
        print("public-source network contract valid")
        return
    request = urllib.request.Request(SEC_SUBMISSIONS, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        latest = latest_periodic(json.load(response))
    apple["latest_detected"] = latest
    if latest["accession"] != apple["source_accession"]:
        apple["review_state"] = "review_required"
        feed["dataset_state"] = "REVIEW_REQUIRED"
    else:
        apple["review_state"] = "current"
        feed["dataset_state"] = "CURRENT_PUBLIC_SOURCE"
    DATA.write_text(json.dumps(feed, indent=2) + "\n")
    print(f"AAPL public-source network: {apple['review_state']} ({latest['form']} {latest['filing_date']})")


if __name__ == "__main__":
    main()
