import importlib.util, json, urllib.request, os
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
os.environ["BUMBLE_DIR"] = str(repo / "bumble")
spec = importlib.util.spec_from_file_location("feed", repo / "scripts/bumble-feed.py")
m = importlib.util.module_from_spec(spec)
real_load = json.load
real_urlopen = urllib.request.urlopen
class Response:
    def read(self): return b"{}"
json.load = lambda handle: {}
urllib.request.urlopen = lambda request, timeout=25: Response()
try: spec.loader.exec_module(m)
finally:
    json.load = real_load
    urllib.request.urlopen = real_urlopen

sample = "DATE,DGS10\n2026-10-13,4.10\n2026-10-14,.\n2026-10-15,4.25\n"
m._get = lambda url, hdr=m.UA, timeout=25: sample.encode()
assert m._fred_latest("DGS10") == (("2026-10-13", 4.10), ("2026-10-15", 4.25))
xml = b'''<rss><channel><item><title>Policy release</title><link>https://www.federalreserve.gov/newsevents/test.htm</link><pubDate>Thu, 15 Oct 2026 14:00:00 GMT</pubDate></item></channel></rss>'''
m._get = lambda url, hdr=m.UA, timeout=25: xml
policy = m.official_policy_updates()
assert len(policy) == 1 and policy[0]["category"] == "policy" and policy[0]["provenance"]["url"].startswith("https://")
events = [{"sender":"T", "category":category, "tkr":str(i), "ts":f"2026-10-{15-i:02d}", "head":f"{category}-{i}"}
          for category in ("equities", "rates", "fx") for i in range(7)]
events.append(dict(events[0]))
out = m.balanced(events, per_category=2, total=6)
assert len(out) == 6
assert {c:sum(x["category"] == c for x in out) for c in ("equities", "rates", "fx")} == {"equities":2, "rates":2, "fx":2}
assert len({x["id"] for x in out}) == len(out)
print("Cross-asset parsing, deduplication, and category balancing passed")
