import re
import json
import subprocess
import unittest
import xml.etree.ElementTree as ET
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


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
        required = {"id", "slug", "name", "repository", "category", "status", "finding", "evidence_date", "methods", "related_products", "corpus_url"}
        corpus = (ROOT / "corpus/index.html").read_text()
        for entry in entries:
            self.assertTrue(required.issubset(entry), entry["slug"])
            self.assertIn(f'id="research-{entry["slug"]}"', corpus)

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


if __name__ == "__main__":
    unittest.main()
