#!/usr/bin/env python3
"""Render one canonical, no-JavaScript navigation block into every public page."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "index.html": "/",
    "start/index.html": "/start/",
    "corpus/index.html": "/corpus/",
    "analysis/index.html": "/analysis/",
    "labs/index.html": "/labs/",
    "capstone/index.html": "/capstone/",
    "block/index.html": "/block/",
    "block/derivatives-honesty.html": None,
    "tracker/index.html": "/tracker/",
    "toolkit/index.html": "/toolkit/",
    "bumble/index.html": "/bumble/",
    "about/index.html": "/about/",
    "404.html": None,
}
LINKS = [
    ("Home", "/"), ("Analysis", "/analysis/"), ("Start here", "/start/"),
    ("System", "/#system"), ("Corpus", "/corpus/"), ("Labs", "/labs/"),
    ("Capstone", "/capstone/"), ("Block", "/block/"), ("Tracker", "/tracker/"),
    ("Toolkit", "/toolkit/"), ("Bumble", "/bumble/"), ("About", "/about/"),
    ("Carter Warrens", "/#carter-warrens"),
]
NAV_RE = re.compile(r'<nav class="bb-site-nav".*?</nav>', re.S)


def navigation(current: str | None) -> str:
    links = []
    for label, href in LINKS:
        marker = ' aria-current="page"' if href == current else ""
        links.append(f'<a href="{href}"{marker}>{label}</a>')
    links.append('<a href="https://github.com/blaquebaux" target="_blank" rel="noopener noreferrer">GitHub ↗</a>')
    return '<nav class="bb-site-nav" aria-label="Site navigation"><div class="bb-nav-inner"><a class="bb-wordmark" href="/">BLAQUE BAUX</a><span class="bb-positioning">Quantitative Intelligence for Finance</span><details class="bb-menu"><summary>Explore</summary><div class="bb-menu-panel">' + "".join(links) + '</div></details></div></nav>'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale = []
    for relative, current in PAGES.items():
        path = ROOT / relative
        source = path.read_text()
        rendered, count = NAV_RE.subn(navigation(current), source, count=1)
        if count != 1:
            raise SystemExit(f"missing navigation block: {relative}")
        if rendered != source:
            if args.check:
                stale.append(relative)
            else:
                path.write_text(rendered)
    if stale:
        raise SystemExit("navigation is out of date: " + ", ".join(stale))


if __name__ == "__main__":
    main()
