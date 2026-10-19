import re
import json
import subprocess
import unittest
import xml.etree.ElementTree as ET
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

from analysis.universe import canonical_ticker, discover_sec_alpaca_universe


ROOT = Path(__file__).resolve().parents[1]
PRIMARY_PAGES = [
    "index.html",
    "start/index.html",
    "corpus/index.html",
    "analysis/index.html",
    "labs/index.html",
    "capstone/index.html",
    "block/index.html",
    "tracker/index.html",
    "toolkit/index.html",
    "bumble/index.html",
    "about/index.html",
    "evidence/index.html",
]
NAV_DESTINATIONS = {
    "/",
    "/start/",
    "/#system",
    "/corpus/",
    "/analysis/",
    "/labs/",
    "/capstone/",
    "/block/",
    "/tracker/",
    "/toolkit/",
    "/bumble/",
    "/about/",
    "/evidence/",
    "/#carter-warrens",
    "https://github.com/blaquebaux",
}


class CorpusStatusParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_status = False
        self.current = ""
        self.statuses = []

    def handle_starttag(self, tag, attrs):
        classes = dict(attrs).get("class", "").split()
        if tag == "span" and "status" in classes:
            self.in_status = True
            self.current = ""

    def handle_data(self, data):
        if self.in_status:
            self.current += data

    def handle_endtag(self, tag):
        if tag == "span" and self.in_status:
            value = " ".join(self.current.split()).replace("● ", "")
            self.statuses.append(value)
            self.in_status = False


class SiteContractTests(unittest.TestCase):
    def test_broad_sec_universe_discovery_is_identity_only(self):
        sec = {
            "0": {"ticker": "CRWV", "title": "CoreWeave, Inc.", "cik_str": 1769628},
            "1": {"ticker": "BRK-B", "title": "Berkshire Hathaway Inc.", "cik_str": 1067983},
        }
        assets = [
            {"symbol": "CRWV", "status": "active", "tradable": True, "exchange": "NASDAQ"},
            {"symbol": "BRK.B", "status": "active", "tradable": True, "exchange": "NYSE"},
            {"symbol": "NOSEC", "status": "active", "tradable": True, "exchange": "NYSE"},
        ]
        with patch("analysis.universe.request_json", side_effect=[sec, assets]):
            universe = discover_sec_alpaca_universe({"APCA-API-KEY-ID": "test"})
        self.assertEqual("BRK.B", canonical_ticker("brk-b"))
        self.assertEqual({"CRWV", "BRK.B"}, set(universe))
        self.assertEqual("0001769628", universe["CRWV"]["cik"])
        self.assertNotIn("sector", universe["CRWV"])

    def test_primary_pages_share_navigation_destinations(self):
        for page in PRIMARY_PAGES:
            text = (ROOT / page).read_text()
            match = re.search(r'<nav class="bb-site-nav".*?</nav>', text, re.S)
            self.assertIsNotNone(match, page)
            destinations = set(re.findall(r'href="([^"]+)"', match.group(0)))
            self.assertEqual(NAV_DESTINATIONS, destinations, page)

    def test_positioning_contract(self):
        home = (ROOT / "index.html").read_text()
        self.assertIn("QUANTITATIVE INTELLIGENCE FOR FINANCE", home)
        self.assertIn("BUILD. VALIDATE. INTEGRATE.", home)
        self.assertIn("A CARTER WARRENS COMPANY", home)
        self.assertNotIn("Proprietary capital deployment is underway", home)

    def test_corpus_counts_reconcile(self):
        corpus = (ROOT / "corpus/index.html").read_text()
        parser = CorpusStatusParser()
        parser.feed(corpus)
        counts = Counter(parser.statuses)
        self.assertEqual(133, len(parser.statuses))
        self.assertEqual(9, counts["LIVE"] + counts["LIVE PATH"] + counts["LIVE DRIVER"])
        self.assertEqual(7, counts["GOVERNED"])
        self.assertEqual(19, counts["VALIDATION"])
        self.assertEqual(33, counts["RESEARCH"])
        self.assertEqual(14, counts["CONCEPT"])
        self.assertEqual(51, counts["NULL"])
        for label in ("Active research / 25", "Meta-sleeves / 14", "Research / 29", "Concept / 14", "Null / graveyard / 51"):
            self.assertIn(label, corpus)

    def test_research_registry_is_current_and_complete(self):
        subprocess.run(["python3", "scripts/build_research_registry.py", "--check"], cwd=ROOT, check=True)
        registry = json.loads((ROOT / "research-registry.json").read_text())
        entries = registry["entries"]
        self.assertEqual(133, len(entries))
        self.assertEqual(133, len({entry["id"] for entry in entries}))
        self.assertEqual(133, len({entry["slug"] for entry in entries}))
        required = {"id", "slug", "name", "repository", "category", "status", "finding", "evidence_date", "methods", "provenance", "related_products", "corpus_url"}
        provenance_required = {"data_window", "benchmark", "costs", "validation_stage", "code_commit", "limitations"}
        corpus = (ROOT / "corpus/index.html").read_text()
        for entry in entries:
            self.assertTrue(required.issubset(entry), entry["slug"])
            self.assertTrue(provenance_required.issubset(entry["provenance"]), entry["slug"])
            self.assertIn(f'id="research-{entry["slug"]}"', corpus)

    def test_generated_navigation_and_accessibility_contracts(self):
        subprocess.run(["python3", "scripts/build_navigation.py", "--check"], cwd=ROOT, check=True)
        subprocess.run(["python3", "scripts/audit_accessibility.py"], cwd=ROOT, check=True)

    def test_release_manifest_contract(self):
        manifest = json.loads((ROOT / "release-manifest.json").read_text())
        self.assertRegex(manifest["site_commit"], r"^[0-9a-f]{40}$")
        self.assertEqual(133, manifest["registry"]["entries"])
        expected = {"research-registry.json", "evidence-readiness.json", "analysis/data.json", "analysis/public-source-network.json", "bumble/feed.json", "bumble/briefings.json", "tracker/performance.json", "tracker/macro.json", "tracker/options.json"}
        self.assertEqual(expected, set(manifest["data_artifacts"]))
        self.assertTrue(all(item["timestamp"] for item in manifest["data_artifacts"].values()))
        self.assertIn("not verified actual performance", manifest["performance_note"])

    def test_phase_three_release_gates_remain_closed(self):
        readiness = json.loads((ROOT / "evidence-readiness.json").read_text())
        self.assertEqual("RESEARCH_ONLY", readiness["release_state"])
        for family in ("actual_performance_gates", "real_time_data_gates"):
            gates = readiness[family]
            self.assertFalse(gates["approved_for_publication"])
        evidence_page = (ROOT / "evidence/index.html").read_text()
        self.assertIn("CURRENT RELEASE / RESEARCH ONLY", evidence_page)
        self.assertIn("No gate opens by implication.", evidence_page)

    def test_homepage_counts_match_registry_taxonomy(self):
        entries = json.loads((ROOT / "research-registry.json").read_text())["entries"]
        operational = sum(entry["status"] in {"LIVE", "LIVE PATH", "LIVE DRIVER"} for entry in entries)
        categories = Counter(entry["category"] for entry in entries)
        home = (ROOT / "index.html").read_text()
        expected = [operational, categories["capstone"], 16, categories["research"] + categories["concept"], categories["null"]]
        for value in expected:
            self.assertRegex(home, rf'<div class="metric"><b>{value}</b>')

    def test_sitemap_covers_primary_pages(self):
        root = ET.parse(ROOT / "sitemap.xml").getroot()
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = {node.text for node in root.findall("sm:url/sm:loc", ns)}
        expected = {
            "https://www.blaquebaux.com/" + ("" if page == "index.html" else page.removesuffix("index.html"))
            for page in PRIMARY_PAGES
        }
        self.assertTrue(expected.issubset(urls))

    def test_bumble_editorial_files_have_no_em_dash(self):
        paths = [ROOT / "bumble/index.html", *sorted((ROOT / "bumble").glob("*.json")), *sorted((ROOT / "bumble/briefings").glob("*.json"))]
        for path in paths:
            self.assertNotIn("—", path.read_text(), str(path.relative_to(ROOT)))

    def test_claim_language_does_not_overstate_performance(self):
        about = (ROOT / "about/index.html").read_text()
        analysis = (ROOT / "analysis/index.html").read_text()
        self.assertNotIn("currently deploying proprietary capital", about)
        self.assertNotIn("attributable live track record now being established", about)
        self.assertIn("not a verified live track record", about)
        self.assertIn("indicative spot", analysis)
        self.assertNotIn("crypto spot is live", analysis)

    def test_analysis_intelligence_contract_and_fixture(self):
        spec = (ROOT / "docs/analysis-intelligence-requirements.md").read_text()
        analysis = (ROOT / "analysis/index.html").read_text()
        fixture = json.loads((ROOT / "analysis/network-fixtures.json").read_text())
        for phrase in (
            "AN-211 economic relationship and consequence map",
            "customer, supplier, lender, borrower, competitor, counterparty",
            "point-in-time",
            "positive, negative, mixed, or indeterminate",
            "second-order",
            "third-order",
            "eligible_sleeves",
            "assigned_sleeve",
            "Inline XBRL",
            "MDRM is used only when an applicable bank regulatory filing",
            "licensed supply-chain datasets",
            "Legal/compliance review",
        ):
            self.assertIn(phrase, spec)
        self.assertNotIn("OPEN AN-211 PREVIEW", analysis)
        self.assertNotIn("Fictional Manufacturer A", analysis)
        self.assertIn("Run verified AAPL network", analysis)
        self.assertIn("Verified anonymous", analysis)
        self.assertIn("Coverage gap", analysis)
        for destination in ("/bumble/", "/corpus/", "/capstone/"):
            self.assertIn(f'href="{destination}"', analysis)
        self.assertEqual("ILLUSTRATIVE_NON_LIVE", fixture["dataset_state"])
        self.assertIn("Not observed market data", fixture["provenance"]["limitations"])
        scenario = fixture["scenarios"][0]
        self.assertIsNone(scenario["sleeve_decision"]["assigned_sleeve"])
        self.assertGreater(len(scenario["sleeve_decision"]["eligible_sleeves"]), 1)
        self.assertIn(2, {item["depth"] for item in scenario["consequences"]})
        self.assertIn(3, {item["depth"] for item in scenario["consequences"]})
        edge_required = {
            "from", "to", "direction", "type", "source", "source_url",
            "valid_from", "valid_to", "confidence", "confidence_rationale",
            "materiality", "materiality_basis", "substitutability",
            "substitutability_rationale",
        }
        for edge in scenario["relationships"]:
            self.assertTrue(edge_required.issubset(edge), edge["id"])
            self.assertEqual("illustrative", edge["evidence_state"])

    def test_public_source_network_contract(self):
        subprocess.run(["python3", "scripts/update_analysis_network.py", "--check"], cwd=ROOT, check=True)
        feed = json.loads((ROOT / "analysis/public-source-network.json").read_text())
        market = json.loads((ROOT / "analysis/data.json").read_text())
        self.assertIn("SPCX", market["meta"])
        self.assertIn("SPCX", market["stats"])
        self.assertIsNone(market["stats"]["SPCX"]["r1y"])
        self.assertTrue({"AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "SPCX"}.issubset(feed["entities"]))
        apple = feed["entities"]["AAPL"]
        self.assertEqual("0000320193", apple["cik"])
        self.assertTrue(apple["source_url"].startswith("https://www.sec.gov/"))
        self.assertEqual("issuer-reported fact", apple["observations"][0]["classification"])
        self.assertTrue(any(edge["identity_state"] == "not disclosed" for edge in apple["relationships"]))
        self.assertTrue(all(edge["source_locator"] for edge in apple["relationships"]))
        self.assertTrue(all("confidence" in edge and "limitations" in edge for edge in apple["relationships"]))
        self.assertTrue(all("hypothesis" in item["confidence"] or "scenario" in item["confidence"] or "independently sourced" in item["confidence"] for item in apple["hypotheses"]))
        for ticker in ("MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "SPCX"):
            entity = feed["entities"][ticker]
            self.assertEqual("structured_only", entity["review_state"])
            self.assertTrue(entity["observations"])
            self.assertEqual([], entity["relationships"])
            self.assertEqual([], entity["hypotheses"])
            self.assertIsNone(entity["assigned_sleeve"])
            self.assertTrue(all("SEC XBRL structured fact" in item["classification"] for item in entity["observations"]))
        analysis = (ROOT / "analysis/index.html").read_text()
        self.assertIn('fetch("data.json"+location.search)', analysis)
        self.assertIn("UNCLASSIFIED / REVIEW PENDING", analysis)
        self.assertIn("Active SEC-mapped US equities enter automatically", analysis)
        self.assertIn("SEC mapped &middot;", analysis)
        self.assertIn("mapped / filing pending", analysis)
        self.assertIn("classification_state", (ROOT / "analysis/build_data.py").read_text())
        self.assertTrue((ROOT / "analysis/universe.py").exists())
        self.assertIn("PUBLIC-SOURCE SEC INTELLIGENCE", analysis)
        self.assertIn("open EDGAR source", analysis)
        self.assertIn('fetch("public-source-network.json"+location.search)', analysis)
        self.assertIn("AUTOMATED XBRL SNAPSHOT", analysis)
        self.assertIn("relationships not reviewed", analysis)
        self.assertIn("No relationship conclusion", analysis)


if __name__ == "__main__":
    unittest.main()
