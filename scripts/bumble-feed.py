#!/usr/bin/python3
# =============================================================================
# bumble-feed.py : builds bumble/feed.json for the live BlaqueBere terminal.
#
# Tier-1 (live now): Form 4 insider clusters + Schedule 13D activists (EDGAR, free) and
# tape movers (Alpaca). Each event is routed through the curated Sleeve Fit table.
# Tier-2 chains, Tier-3 dominoes, and the briefs are left as empty senders the page
# already supports; they get wired in later. Rolling ~2-day window, regenerated each run.
#
# stdlib only (urllib/json/xml) plus the Alpaca screener; no pip installs on the runner.
# Env: ALPACA_KEY_ID, ALPACA_SECRET_KEY.  BUMBLE_DIR points at the folder holding
# sleeve_exposure.json and receiving feed.json (default: this script's directory).
# =============================================================================
import os, json, re, time, urllib.request
from collections import defaultdict
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("BUMBLE_DIR", HERE)
UA = {"User-Agent": "Blaque Baux Research ceo@carterwarrens.com"}
AL = {"APCA-API-KEY-ID": os.environ.get("ALPACA_KEY_ID", ""), "APCA-API-SECRET-KEY": os.environ.get("ALPACA_SECRET_KEY", "")}

def _get(url, hdr=UA, timeout=25):
    return urllib.request.urlopen(urllib.request.Request(url, headers=hdr), timeout=timeout).read()
def _getj(url, hdr=UA):
    return json.loads(_get(url, hdr))

TABLE = json.load(open(os.path.join(OUT, "sleeve_exposure.json")))
CIK2TK = {int(v["cik_str"]): v["ticker"] for v in _getj("https://www.sec.gov/files/company_tickers.json").values()}

# ---------------------------------------------------------------- Sleeve Fit router
CRED = {"live", "keeper", "validation"}
NONEQUITY = {"muni", "credit", "commodity", "rates", "fx", "crypto", "em_intl"}
def _route(asset, factors, max_each=5):
    with_, against, na = [], [], []
    for name, v in TABLE.items():
        a, styles, role, status = v["asset_class"], set(v["styles"]), v["role"], v["status"]
        if role == "capstone/allocator": continue
        is_hedge = role == "hedge/short" or "tail/hedge" in styles
        cred = 2 if status in CRED else 0
        if asset == "equity":
            if a == "equity" and role == "long-beta" and not is_hedge: with_.append((sum(f in styles for f in factors) + cred, name))
            elif is_hedge and a in ("equity", "vol_options"): against.append((cred + ("tail/hedge" in styles), name))
            elif a in NONEQUITY: na.append((0, name))
        else:
            if a == asset and not is_hedge: with_.append((sum(f in styles for f in factors) + cred, name))
            elif a == asset and is_hedge: against.append((cred, name))
            else: na.append((0, name))
    pick = lambda L: [n for _, n in sorted(L, key=lambda x: -x[0])[:max_each]]
    return pick(with_), pick(against), pick(na)

def sleeve_fit(asset, direction, factors):
    longs, hedges, na = _route(asset, factors)
    if direction == "bearish":
        return {"with": hedges, "against": longs, "na": na,
                "intro": "Bumble does not grade the news; it routes it. To act on a bearish read, here are the vehicles. Your strategy decides."}
    return {"with": longs, "against": hedges, "na": na,
            "intro": "Bumble does not grade the news; it routes it. To act on a bullish read, here are the vehicles. Your strategy decides."}

# ---------------------------------------------------------------- helpers
def fmt_date(d):   # "2026-10-09" -> "October 9, 2026"
    return datetime.strptime(d, "%Y-%m-%d").strftime("%B %-d, %Y")
def usd(x): return f"${x:,.0f}"

# ---------------------------------------------------------------- Form 4 clusters
def fts_form4(start, end, pages=40):
    hits = []
    for p in range(pages):
        try: d = _getj(f"https://efts.sec.gov/LATEST/search-index?forms=4&startdt={start}&enddt={end}&from={p*10}")
        except Exception: break
        hs = d["hits"]["hits"]
        if not hs: break
        hits += hs; time.sleep(0.1)
    return hits

def parse_f4(xmlb):
    r = ET.fromstring(xmlb); g = lambda p: (r.find(p).text if r.find(p) is not None else None)
    role = []
    if g('.//isDirector') in ('1', 'true'): role.append('Dir')
    if g('.//isTenPercentOwner') in ('1', 'true'): role.append('10%')
    if g('.//isOfficer') in ('1', 'true'): role.append((g('.//officerTitle') or 'Officer').strip())
    txns = []
    for tr in r.findall('.//nonDerivativeTransaction'):
        c = tr.find('.//transactionCode'); sh = tr.find('.//transactionShares/value'); px = tr.find('.//transactionPricePerShare/value')
        txns.append((c.text if c is not None else '?', float(sh.text) if (sh is not None and sh.text) else 0.0, float(px.text) if (px is not None and px.text) else 0.0))
    return (g('.//rptOwnerName') or '?'), ("/".join(role) or '?'), txns, (g('.//periodOfReport') or '')

def insider_clusters(start, end, limit=8):
    hits = fts_form4(start, end)
    by = defaultdict(lambda: defaultdict(list)); names = {}
    for h in hits:
        icik = tkr = None
        for c in h["_source"]["ciks"]:
            if int(c) in CIK2TK: icik, tkr = int(c), CIK2TK[int(c)]; break
        if not tkr: continue
        names[tkr] = next((n for c, n in zip(h["_source"]["ciks"], h["_source"]["display_names"]) if int(c) == icik), tkr)
        owner = next((c for c in h["_source"]["ciks"] if int(c) != icik), h["_source"]["ciks"][0])
        by[tkr][owner].append(h)
    cand = sorted([(t, d) for t, d in by.items() if len(d) >= 2], key=lambda x: -len(x[1]))
    events = []; budget = 110
    for tkr, owners in cand:
        agg = defaultdict(lambda: [0.0, 0.0]); roles = {}; dt = ""
        for ocik, hs in owners.items():
            if budget <= 0: break
            adsh = hs[0]["_source"]["adsh"]; fn = hs[0]["_id"].split(":", 1)[1].split("/")[-1]
            try:
                owner, role, txns, per = parse_f4(_get(f"https://www.sec.gov/Archives/edgar/data/{int(adsh.split('-')[0])}/{adsh.replace('-','')}/{fn}")); budget -= 1; time.sleep(0.07)
            except Exception: continue
            roles[owner] = role; dt = hs[0]["_source"]["file_date"]
            for code, sh, px in txns:
                if code == 'P': agg[owner][0] += sh * px
                elif code == 'S': agg[owner][1] += sh * px
        buyers = {o: v[0] for o, v in agg.items() if v[0] > 0}; sellers = {o: v[1] for o, v in agg.items() if v[1] > 0}
        who = set(buyers) | set(sellers)
        if len(who) < 2: continue
        buy = sum(buyers.values()) >= sum(sellers.values())
        side = buyers if buy else sellers; tot = sum(side.values())
        nm = names[tkr]
        top = sorted(side.items(), key=lambda x: -x[1])[:5]
        events.append({
            "sender": "EDGAR", "chip": "EDGAR · 4", "tkr": tkr, "cls": "buy" if buy else "sell",
            "date": fmt_date(dt), "ts": dt, "time": dt[5:],
            "head": f"{len(who)} insiders {'bought' if buy else 'sold'} {usd(tot)} open-market" + (" incl. the CFO" if any('CFO' in r or 'Chief Financial' in r for r in roles.values()) else ""),
            "note": ("Cluster buys skew bullish; strongest when the CFO or CEO leads." if buy else "Cluster selling by multiple insiders; context matters, but a tell worth watching."),
            "evi": "insider cluster · modest documented edge",
            "detail": {
                "kicker": "EDGAR · FORM 4 · INSIDER CLUSTER", "title": f"{tkr} · {len(who)} insiders {'buy' if buy else 'sell'} {usd(tot)}",
                "sub": f"{nm} · open-market P/S · filed {dt}",
                "sections": [{"h": "Who", "list": [f"{o} ({roles.get(o,'?')}) {usd(a)}" for o, a in top]}],
                "pri": ("Potential outcome: mild positive drift; size as a tilt, not a thesis. Confirm the buys continue." if buy else "Potential outcome: a distribution tell; confirm against the tape and any 8-K."),
            },
            "fit": sleeve_fit("equity", "bullish" if buy else "bearish", {"momentum/trend", "quality", "macro/regime"}),
        })
        if budget <= 0 or len(events) >= limit: break
    return events

# ---------------------------------------------------------------- 13D activist
def daily_13d(dates, limit=8):
    rows = []
    for dt in dates:
        y, q = dt[:4], (int(dt[4:6]) - 1) // 3 + 1
        try: idx = _get(f"https://www.sec.gov/Archives/edgar/daily-index/{y}/QTR{q}/master.{dt}.idx").decode('latin-1')
        except Exception: continue
        for line in idx.splitlines():
            p = line.split("|")
            if len(p) == 5 and p[2].startswith("SCHEDULE 13D"):
                rows.append((p[3], p[2], int(p[0]), p[1], p[4]))
    events = []; seen = set()
    for raw_dt, form, subjcik, subjname, path in rows:
        tkr = CIK2TK.get(subjcik)
        if not tkr or tkr in seen: continue
        seen.add(tkr)
        try:
            txt = _get("https://www.sec.gov/Archives/" + path).decode('latin-1', 'ignore')[:7000]; time.sleep(0.08)
            b = txt.split("FILED BY:"); who = (re.search(r"COMPANY CONFORMED NAME:\s*(.+)", b[1]).group(1).strip() if len(b) > 1 else "?")
        except Exception: who = "?"
        new = form == "SCHEDULE 13D"
        d = f"{raw_dt[:4]}-{raw_dt[4:6]}-{raw_dt[6:]}"
        events.append({
            "sender": "EDGAR", "chip": "EDGAR · 13D" + ("" if new else "/A"), "tkr": tkr, "cls": "buy",
            "date": fmt_date(d), "ts": d, "time": d[5:],
            "head": f"{who} {'discloses a new' if new else 'adds to a'} stake" + (" (new activist)" if new else " (accumulation)"),
            "note": "13D signals intent to influence: a board push, capital return, or a sale. Announcement pop, then board-dependent.",
            "evi": "activist · real pop, fades",
            "detail": {"kicker": "EDGAR · SC 13D · ACTIVIST", "title": f"{tkr} · {who}", "sub": f"{subjname} · {'new Schedule 13D' if new else 'amendment (accumulation)'} · {d}",
                       "sections": [{"h": "Read", "p": "A 13D (not a passive 13G) puts an activist on the register with stated intent. Typical playbook: cost cuts, capital return, a strategic review, or a sale."}],
                       "pri": "Potential outcome: initial pop, then path-dependent on the board's response; the documented activist premium fades without a catalyst."},
            "fit": sleeve_fit("equity", "bullish", {"event/activist", "macro/regime"}),
        })
        if len(events) >= limit: break
    return events

# ---------------------------------------------------------------- tape movers (Alpaca)
WARRANT = re.compile(r"(W|U|R|WS|RT)$")
def clean_sym(s): return bool(re.fullmatch(r"[A-Z]{1,5}", s)) and not WARRANT.search(s[-2:])
def movers(limit=6):
    if not AL["APCA-API-KEY-ID"]: return []
    try: m = _getj("https://data.alpaca.markets/v1beta1/screener/stocks/movers?top=25", AL)
    except Exception: return []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d"); dlabel = fmt_date(today)
    evs = []
    for side, cls, dirn in (("gainers", "watch", "up"), ("losers", "watch", "dn")):
        n = 0
        for row in m.get(side, []):
            s = row["symbol"]; pc = row["percent_change"]; px = row["price"]
            if not clean_sym(s) or px < 10 or abs(pc) < 7 or abs(pc) > 75: continue
            evs.append({
                "sender": "TAPE", "chip": "TAPE", "tkr": s, "cls": cls, "pct": f"{pc:+.0f}%", "pdir": dirn,
                "date": dlabel, "ts": today + ("T23:58" if side == "gainers" else "T23:57"), "time": "today",
                "head": f"{'Top gainer' if side=='gainers' else 'Top decliner'}: {pc:+.0f}% to ${px:,.2f}",
                "note": "A large move; cross-check EDGAR for a filing that explains it. A watch, not a confirm.",
                "evi": "unusual activity · unconfirmed",
                "detail": {"kicker": "TAPE · UNUSUAL ACTIVITY", "title": f"{s} · {pc:+.0f}% to ${px:,.2f}", "sub": f"top {'gainer' if side=='gainers' else 'decliner'} · {dlabel}",
                           "sections": [{"h": "Read", "p": "A large move; Bumble cross-references the EDGAR stream and flags if a Form 4 or 8-K lands to explain it. Mean-reversion risk if it is positioning-driven."}],
                           "pri": "Potential outcome: only promote to a tilt if a filing or confirmed catalyst follows."},
                "fit": sleeve_fit("equity", "bullish" if dirn == "up" else "bearish", {"momentum/trend"}),
            })
            n += 1
            if n >= limit // 2: break
    return evs

# ---------------------------------------------------------------- build
def run():
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    f4_start = (now - timedelta(days=4)).strftime("%Y-%m-%d"); f4_end = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    d13 = [(now - timedelta(days=i)).strftime("%Y%m%d") for i in range(0, 4)]
    events = []
    try: events += insider_clusters(f4_start, f4_end)
    except Exception as e: print("insider error:", e)
    try: events += daily_13d(d13)
    except Exception as e: print("13d error:", e)
    try: events += movers()
    except Exception as e: print("movers error:", e)
    for i, ev in enumerate(events): ev["id"] = f"ev{i}"
    events.sort(key=lambda e: e["ts"], reverse=True)
    feed = {"generated_at": now.isoformat(timespec="seconds"), "count": len(events), "events": events}
    with open(os.path.join(OUT, "feed.json"), "w") as f: json.dump(feed, f, indent=1)
    print(f"wrote {OUT}/feed.json : {len(events)} events  ({sum(e['sender']=='EDGAR' and '4' in e['chip'] for e in events)} insider, "
          f"{sum('13D' in e['chip'] for e in events)} activist, {sum(e['sender']=='TAPE' for e in events)} tape)")

if __name__ == "__main__":
    run()
