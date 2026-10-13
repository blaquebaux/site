#!/usr/bin/env python3
"""Dependency-free accessibility contract checks for public static pages."""

from html.parser import HTMLParser
from pathlib import Path

from build_navigation import PAGES, ROOT


class AuditParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.images_without_alt = 0
        self.nav_labels = []
        self.summaries = 0
        self.html_lang = None
        self.viewport = False

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "html":
            self.html_lang = values.get("lang")
        if tag == "img" and "alt" not in values:
            self.images_without_alt += 1
        if tag == "nav":
            self.nav_labels.append(values.get("aria-label"))
        if tag == "summary":
            self.summaries += 1
        if tag == "meta" and values.get("name") == "viewport":
            self.viewport = True


def main() -> None:
    failures = []
    for relative in PAGES:
        source = (ROOT / relative).read_text()
        parser = AuditParser()
        parser.feed(source)
        duplicates = sorted({item for item in parser.ids if parser.ids.count(item) > 1})
        if parser.html_lang != "en": failures.append(f"{relative}: html lang must be en")
        if parser.images_without_alt: failures.append(f"{relative}: {parser.images_without_alt} image(s) missing alt")
        if duplicates: failures.append(f"{relative}: duplicate ids {duplicates}")
        if "Site navigation" not in parser.nav_labels: failures.append(f"{relative}: navigation needs an accessible label")
        if parser.summaries < 1: failures.append(f"{relative}: navigation disclosure needs a summary")
        if not parser.viewport: failures.append(f"{relative}: viewport metadata missing")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"Accessibility contracts passed for {len(PAGES)} public pages")


if __name__ == "__main__":
    main()
