#!/usr/bin/env python3
"""Build and verify the public research registry from the rendered Corpus."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "corpus/index.html"
REGISTRY = ROOT / "research-registry.json"
EVIDENCE_DATE = "2026-10-09"
PRODUCT_PAGES = {
    "analysis": ROOT / "analysis/index.html",
    "labs": ROOT / "labs/index.html",
    "capstone": ROOT / "capstone/index.html",
    "tracker": ROOT / "tracker/index.html",
    "toolkit": ROOT / "toolkit/index.html",
    "block": ROOT / "block/index.html",
}


ENTRY_RE = re.compile(
    r'<a class="repo repo-explained"(?P<attrs>[^>]*)>'
    r'<span class="num">(?P<number>[^<]+)</span>'
    r'<span class="name">(?P<name>[^<]+)</span>'
    r'<span class="repo-copy"><span class="desc">(?P<description>.*?)</span>'
    r'<span class="why [^"]+"><strong>(?P<label>[^<]+)</strong>\s*(?P<finding>.*?)</span></span>'
    r'<span class="status [^"]+">(?P<status>.*?)</span></a>'
)


def clean(value: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", value)).split())


def category(number: int) -> str:
    if number <= 25:
        return "active"
    if number <= 39:
        return "capstone"
    if number <= 68:
        return "research"
    if number <= 82:
        return "concept"
    return "null"


def related_products(repository: str) -> list[str]:
    needle = f"github.com/blaquebaux/{repository}"
    return [name for name, path in PRODUCT_PAGES.items() if needle in path.read_text()]


def build() -> dict:
    source = CORPUS.read_text()
    entries = []
    for match in ENTRY_RE.finditer(source):
        attrs = match.group("attrs")
        href_match = re.search(r'href="([^"]+)"', attrs)
        if not href_match:
            raise ValueError(f"Corpus entry {match.group('number')} has no repository URL")
        repository_url = href_match.group(1)
        repository = repository_url.rstrip("/").split("/")[-1]
        number = int(clean(match.group("number")))
        entries.append(
            {
                "id": f"{number:03d}",
                "slug": repository,
                "name": clean(match.group("name")),
                "repository": repository_url,
                "category": category(number),
                "status": clean(match.group("status")).removeprefix("● "),
                "description": clean(match.group("description")),
                "finding": clean(match.group("finding")),
                "evidence_date": EVIDENCE_DATE,
                "methods": repository_url + "#readme",
                "provenance": {
                    "data_window": "Not standardized in the site registry; see repository methods.",
                    "benchmark": "Not standardized in the site registry; see repository methods.",
                    "costs": "Not standardized in the site registry; see repository methods.",
                    "validation_stage": clean(match.group("status")).removeprefix("● "),
                    "code_commit": None,
                    "limitations": "Site summary only. Repository assumptions and results have not been independently reproduced for this release.",
                },
                "related_products": related_products(repository),
                "corpus_url": f"/corpus/#research-{repository}",
            }
        )
    if len(entries) != 133:
        raise ValueError(f"Expected 133 Corpus entries, found {len(entries)}")
    return {
        "schema_version": 2,
        "generated_at": "2026-10-13",
        "source": "/corpus/",
        "evidence_date": EVIDENCE_DATE,
        "status_note": "LIVE labels describe operational research maturity, not verified actual performance.",
        "entries": entries,
    }


def add_anchors(source: str, registry: dict) -> str:
    for entry in registry["entries"]:
        anchor = f'id="research-{entry["slug"]}"'
        if anchor in source:
            continue
        url = re.escape(entry["repository"])
        pattern = rf'(<a class="repo repo-explained")( href="{url}")'
        replacement = rf'\1 id="research-{entry["slug"]}"\2'
        source, count = re.subn(pattern, replacement, source, count=1)
        if count != 1:
            raise ValueError(f"Could not attach Corpus anchor for {entry['slug']}")
    return source


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated files differ")
    args = parser.parse_args()
    registry = build()
    registry_text = json.dumps(registry, indent=2, ensure_ascii=False) + "\n"
    corpus_text = add_anchors(CORPUS.read_text(), registry)
    if args.check:
        if not REGISTRY.exists() or REGISTRY.read_text() != registry_text:
            raise SystemExit("research-registry.json is out of date")
        if CORPUS.read_text() != corpus_text:
            raise SystemExit("Corpus anchors are out of date")
        return
    REGISTRY.write_text(registry_text)
    CORPUS.write_text(corpus_text)


if __name__ == "__main__":
    main()
