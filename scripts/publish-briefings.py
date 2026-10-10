#!/usr/bin/env python3
"""Validate reviewed editorial inputs and atomically build the terminal archive."""
import json, re, sys
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
KINDS = {"morning": "PULSE", "afternoon": "PULSE", "weekly": "WEEKLY"}

def validate(a, now):
    assert re.fullmatch(r"[a-z0-9][a-z0-9-]{2,100}", a["id"]), "invalid id"
    assert a["kind"] in KINDS, "invalid edition"
    assert a["status"] in ("verified", "mock", "archived-unverified"), "status must be verified, mock, or archived-unverified"
    for k in ("title", "summary", "reviewed_by"):
        assert isinstance(a[k], str) and a[k].strip(), f"missing {k}"
    t = datetime.fromisoformat(a["published_at"])
    assert t.tzinfo and t <= now, "publication needs an offset and cannot be future dated"
    local = t.astimezone(ET)
    assert local.weekday() == 5 if a["kind"] == "weekly" else local.weekday() < 5, "wrong edition day in ET"
    observed = datetime.fromisoformat(a["observed_at"])
    assert observed.tzinfo and observed <= t, "invalid observation timestamp"
    assert a["sections"] and all(s.get("heading") and (s.get("paragraphs") or s.get("list")) for s in a["sections"]), "empty sections"
    assert a["sources"], "source links required"
    for source in a["sources"]:
        assert source.get("label") and re.match(r"^https://[^/\s]+(?:/|$)", source["url"]), "invalid source link"
    # Editorial choice is explicit per article; headings generally take a colon.
    punctuation = a.get("dash_replacement", ";")
    assert punctuation in (";", ":"), "choose colon or semicolon"
    def normalize(value):
        if isinstance(value, str):
            assert not re.search(r"chatgpt-content-reference|||", value), "unresolved citation/entity"
            return re.sub(r"\s*—\s*", punctuation + " ", value)
        if isinstance(value, list): return [normalize(x) for x in value]
        if isinstance(value, dict): return {k: v if k == "url" else normalize(v) for k,v in value.items()}
        return value
    return normalize(a)

def build(root, now=None):
    now = now or datetime.now(timezone.utc)
    articles = [validate(json.loads(f.read_text()), now) for f in sorted((root / "briefings").glob("*.json"))]
    assert len({a["id"] for a in articles}) == len(articles), "duplicate article id"
    articles.sort(key=lambda a: datetime.fromisoformat(a["published_at"]), reverse=True)
    out = root / "briefings.json"
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps({"schema_version":1, "articles":articles}, indent=2) + "\n")
    tmp.replace(out)
    return articles

if __name__ == "__main__":
    try:
        print(f"Published {len(build(Path(sys.argv[1] if len(sys.argv)>1 else 'bumble')))} reviewed briefings")
    except (AssertionError, KeyError, ValueError, TypeError) as error:
        sys.exit(f"Briefing validation failed: {error}")
