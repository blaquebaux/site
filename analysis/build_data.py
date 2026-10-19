#!/usr/bin/python3
# =============================================================================
# build_data.py - refreshes analysis/data.json for the /analysis/ page.
#
# Pulls ~2y daily bars for the universe from Alpaca (equities SIP + crypto), regresses each ticker on a
# factor basis for real factor loadings, computes trailing stats + a trend/momentum scorecard and a
# global macro-regime read, and writes a same-origin data.json the static page consumes (no CORS, no
# keys in the browser). Run daily (cron or GitHub Action with ALPACA_* secrets), then commit data.json.
#   ALPACA_KEY_ID / ALPACA_SECRET_KEY in env.  python3 analysis/build_data.py
# =============================================================================
import os, json, math, urllib.request, urllib.parse, datetime, time
import numpy as np

def fetch(u, tries=6):
    for a in range(tries):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=90))
        except urllib.error.HTTPError as e:
            if e.code in (403,429) and a<tries-1: time.sleep(2**a); continue
            raise

H={"APCA-API-KEY-ID":os.environ["ALPACA_KEY_ID"],"APCA-API-SECRET-KEY":os.environ["ALPACA_SECRET_KEY"],"User-Agent":"bb-analysis/1.0"}
START=(datetime.date.today()-datetime.timedelta(days=760)).isoformat()
END=(datetime.date.today()-datetime.timedelta(days=1)).isoformat()  # basic SIP plan blocks querying up to today

# ---- universe metadata (single source of truth; the page loads this) ----------------
# T: (name, class, sector, [[sleeveLabel,repo]...], skewTag(-1/0/1), riskNote)
def S(*p): return list(p)
U={
 # broad / index
 "SPY":S("S&P 500","US index","Broad",[["bogle","bogle"]],0,"market beta"),
 "VTI":S("US total market","US index","Broad",[["bogle","bogle"]],0,"market beta"),
 "QQQ":S("Nasdaq 100","US index","Growth",[["broad","broad"],["bull","bull"]],-1,"growth beta, deeper drawdowns"),
 "DIA":S("Dow 30","US index","Broad",[["bogle","bogle"]],0,"large-cap beta"),
 "IWM":S("Russell 2000","US index","Small cap",[["bogle","bogle"]],-1,"small-cap beta, higher vol"),
 "RSP":S("S&P equal weight","US index","Broad",[["bogle","bogle"]],0,"equal-weight beta"),
 "MDY":S("S&P MidCap 400","US index","Mid cap",[["bogle","bogle"]],-1,"mid-cap beta"),
 # factor
 "MTUM":S("Momentum factor","Factor ETF","Momentum",[["boom","boom"],["bulwark","bulwark"]],-1,"momentum, crash-prone"),
 "QUAL":S("Quality factor","Factor ETF","Quality",[["buffett","buffett"],["blemish","blemish"]],0,"quality ~ SPY-like"),
 "VLUE":S("Value factor","Factor ETF","Value",[["balanced","balanced"]],0,"value, regime-dependent"),
 "USMV":S("Min-volatility","Factor ETF","Low-vol",[["bunker","bunker"]],0,"low-vol defensive"),
 "SPLV":S("Low volatility","Factor ETF","Low-vol",[["bunker","bunker"]],0,"low-vol defensive"),
 "SIZE":S("Size factor","Factor ETF","Size",[["bogle","bogle"]],-1,"size tilt"),
 # sectors
 "XLK":S("Technology","Sector ETF","Technology",[["broad","broad"]],-1,"growth/tech beta"),
 "XLF":S("Financials","Sector ETF","Financials",[["basel","basel"]],-1,"banks ~ one rate factor"),
 "XLE":S("Energy","Sector ETF","Energy",[["barrel","barrel"]],-1,"commodity/energy beta"),
 "XLV":S("Healthcare","Sector ETF","Healthcare",[["bio","bio"]],0,"defensive-ish sector"),
 "XLP":S("Staples","Sector ETF","Staples",[["belt-tighteners","belt-tighteners"]],1,"defensive, holds in stress"),
 "XLU":S("Utilities","Sector ETF","Utilities",[["bunker","bunker"]],0,"rate-sensitive defensive"),
 "XLY":S("Discretionary","Sector ETF","Discretionary",[["broad","broad"]],-1,"cyclical beta"),
 "XLI":S("Industrials","Sector ETF","Industrials",[["bigbrother","bigbrother"]],-1,"cyclical beta"),
 "XLB":S("Materials","Sector ETF","Materials",[["barrel","barrel"]],-1,"cyclical / commodity"),
 "XLRE":S("Real estate","Sector ETF","Real estate",[["brownstone","brownstone"]],-1,"equity + duration beta"),
 "XLC":S("Communication","Sector ETF","Communication",[["broad","broad"]],-1,"growth/comm beta"),
 "SMH":S("Semiconductors","Industry ETF","Semis",[["broad","broad"]],-1,"high-beta semis"),
 "SOXX":S("Semiconductors","Industry ETF","Semis",[["broad","broad"]],-1,"high-beta semis"),
 "IGV":S("Software","Industry ETF","Software",[["broad","broad"]],-1,"high-beta software"),
 "XBI":S("Biotech","Industry ETF","Biotech",[["bio","bio"]],-1,"idiosyncratic, high dispersion"),
 "KRE":S("Regional banks","Industry ETF","Banks",[["basel","basel"]],-1,"rate/credit-sensitive banks"),
 "ITB":S("Homebuilders","Industry ETF","Homebuild",[["brownstone","brownstone"]],-1,"rate-sensitive cyclical"),
 "XOP":S("Oil & gas E&P","Industry ETF","Energy",[["barrel","barrel"]],-1,"high-beta energy"),
 "JETS":S("Airlines","Industry ETF","Airlines",[["battered","battered"]],-1,"deep cyclical, crisis-fragile"),
 "XME":S("Metals & mining","Industry ETF","Materials",[["barrel","barrel"]],-1,"commodity cyclical"),
 "IYT":S("Transports","Industry ETF","Transport",[["bellwether","bellwether"]],-1,"cyclical bellwether"),
 # bonds / rates
 "TLT":S("20y+ Treasuries","Bond ETF","Long duration",[["binnacle","binnacle"],["backstop","backstop"]],1,"long duration, rate bet"),
 "EDV":S("Extended duration","Bond ETF","Long duration",[["binnacle","binnacle"]],1,"very long duration"),
 "IEF":S("7-10y Treasuries","Bond ETF","Duration",[["binnacle","binnacle"]],1,"intermediate duration"),
 "SHY":S("1-3y Treasuries","Bond ETF","Short duration",[["bide","bide"]],0,"near-cash"),
 "BIL":S("T-bills","Bond ETF","Cash",[["bide","bide"]],0,"cash, no risk premium"),
 "GOVT":S("US Treasuries","Bond ETF","Duration",[["binnacle","binnacle"]],1,"broad Treasury duration"),
 "AGG":S("US aggregate","Bond ETF","Core bonds",[["bands","bands"]],0,"core bond beta"),
 "BND":S("US total bond","Bond ETF","Core bonds",[["bands","bands"]],0,"core bond beta"),
 "TIP":S("TIPS","Bond ETF","Inflation",[["belt-tighteners","belt-tighteners"]],0,"real-rate / inflation"),
 "LQD":S("IG credit","Bond ETF","Credit",[["bedrock","bedrock"]],-1,"credit spread, crash-correlated"),
 "HYG":S("High-yield credit","Bond ETF","Credit",[["bedrock","bedrock"],["battered","battered"]],-1,"HY spread, equity-like tail"),
 "JNK":S("High-yield credit","Bond ETF","Credit",[["bedrock","bedrock"]],-1,"HY spread tail"),
 "BKLN":S("Leveraged loans","Bond ETF","Private credit",[["bedrock","bedrock"]],-1,"floating-rate credit, liquidity tail"),
 "EMB":S("EM debt","Bond ETF","Credit / EM",[["bazaar","bazaar"]],-1,"short-dollar carry, crash tail"),
 "MUB":S("Municipals","Bond ETF","Muni",[["borough","borough"]],0,"tax-advantaged carry"),
 "PFF":S("Preferreds","Bond ETF","Hybrids",[["bowed","bowed"]],-1,"levered credit+duration tail"),
 # real assets
 "GLD":S("Gold","Commodity ETF","Gold",[["bullion","bullion"]],1,"hard-money diversifier"),
 "IAU":S("Gold","Commodity ETF","Gold",[["bullion","bullion"]],1,"hard-money diversifier"),
 "SLV":S("Silver","Commodity ETF","Precious",[["bullion","bullion"]],-1,"higher-beta precious"),
 "GDX":S("Gold miners","Commodity ETF","Gold",[["bullion","bullion"]],-1,"1.9x-levered gold, drag"),
 "GDXJ":S("Junior gold miners","Commodity ETF","Gold",[["bullion","bullion"]],-1,"high-beta miners"),
 "DBC":S("Broad commodities","Commodity ETF","Commodity",[["barrel","barrel"],["bounty","bounty"]],0,"commodity beta"),
 "USO":S("Crude oil","Commodity ETF","Energy",[["barrel","barrel"]],-1,"contango bleed"),
 "UNG":S("Natural gas","Commodity ETF","Energy",[["bonfire","bonfire"]],-1,"heavy contango bleed"),
 "DBA":S("Agriculture","Commodity ETF","Agriculture",[["bonfire","bonfire"]],0,"ag commodity beta"),
 "URA":S("Uranium","Commodity ETF","Energy",[["barrel","barrel"]],-1,"thematic energy, high vol"),
 # real estate
 "VNQ":S("US REITs","Real-estate ETF","Real estate",[["brownstone","brownstone"]],-1,"equity+duration, not a diversifier"),
 "IYR":S("US REITs","Real-estate ETF","Real estate",[["brownstone","brownstone"]],-1,"equity+duration beta"),
 "SCHH":S("US REITs","Real-estate ETF","Real estate",[["brownstone","brownstone"]],-1,"equity+duration beta"),
 "REM":S("Mortgage REITs","Real-estate ETF","Real estate",[["brownstone","brownstone"]],-1,"-70% drawdown yield landmine"),
 "REZ":S("Residential REITs","Real-estate ETF","Real estate",[["boulevard","boulevard"]],-1,"REIT sub-sector"),
 # international
 "EFA":S("Developed ex-US","Intl ETF","Developed",[["emea","emea"]],-1,"US beta wearing a flag"),
 "VEA":S("Developed ex-US","Intl ETF","Developed",[["emea","emea"]],-1,"US beta + FX drag"),
 "EEM":S("Emerging markets","Intl ETF","EM",[["brics","brics"]],-1,"EM beta, short-dollar"),
 "VWO":S("Emerging markets","Intl ETF","EM",[["brics","brics"]],-1,"EM beta"),
 "FXI":S("China large-cap","Intl ETF","China",[["brics","brics"]],-1,"China beta, policy tail"),
 "EWJ":S("Japan","Intl ETF","Japan",[["emea","emea"]],-1,"Japan beta + FX"),
 "EWZ":S("Brazil","Intl ETF","LatAm",[["latam","latam"]],-1,"EM beta, commodity/FX tail"),
 "INDA":S("India","Intl ETF","India",[["brics","brics"]],-1,"EM growth beta"),
 "ILF":S("Latin America","Intl ETF","LatAm",[["latam","latam"]],-1,"EM beta"),
 # crypto (spot via crypto API)
 "BTC":S("Bitcoin","Crypto","Crypto",[["bitdollar","bitdollar"]],-1,"crypto beta, fat tails"),
 "ETH":S("Ethereum","Crypto","Crypto",[["bitdollar","bitdollar"],["brash","brash"]],-1,"higher-beta crypto"),
 "SOL":S("Solana","Crypto","Crypto",[["brash","brash"]],-1,"high-beta crypto"),
 "IBIT":S("Bitcoin ETF","Crypto ETF","Crypto",[["bitdollar","bitdollar"]],-1,"spot BTC"),
 "BITO":S("Bitcoin futures ETF","Crypto ETF","Crypto",[["bitdollar","bitdollar"]],-1,"BTC + roll"),
 "ETHA":S("Ethereum ETF","Crypto ETF","Crypto",[["brash","brash"]],-1,"spot ETH"),
 "COIN":S("Coinbase","Crypto equity","Crypto",[["byproduct","byproduct"]],-1,"levered crypto proxy"),
 "MSTR":S("MicroStrategy","Crypto equity","Crypto",[["byproduct","byproduct"]],-1,"levered BTC proxy, extreme tail"),
 "MARA":S("Marathon","Crypto equity","Crypto",[["byproduct","byproduct"]],-1,"BTC miner, extreme beta"),
 "RIOT":S("Riot","Crypto equity","Crypto",[["byproduct","byproduct"]],-1,"BTC miner, extreme beta"),
 # vol / liquid alts / structure / leverage
 "VIXM":S("Mid-term VIX","Volatility ETF","Long-vol",[["bleed","bleed"]],1,"convex tail hedge, bleeds"),
 "VXZ":S("Mid-term VIX","Volatility ETF","Long-vol",[["bleed","bleed"]],1,"convex tail hedge"),
 "VXX":S("Short-term VIX","Volatility ETF","Long-vol",[["bleed","bleed"]],1,"convex, heavy bleed"),
 "UVXY":S("1.5x VIX","Volatility ETF","Long-vol",[["bleed","bleed"]],1,"levered vol, severe bleed"),
 "SVXY":S("Short VIX","Volatility ETF","Short-vol",[["bravado","bravado"],["bushel","bushel"]],-1,"short-vol ruin shape"),
 "DIVO":S("Covered-call income","Income ETF","Buy-write",[["bankroll","bankroll"]],-1,"income, caps upside"),
 "JEPI":S("Equity premium income","Income ETF","Buy-write",[["bankroll","bankroll"]],-1,"income, caps upside"),
 "JEPQ":S("Nasdaq premium income","Income ETF","Buy-write",[["bankroll","bankroll"]],-1,"income on growth, caps upside"),
 "PUTW":S("Put-write","Income ETF","Short-vol",[["bankroll","bankroll"],["bodega","bodega"]],-1,"sells vol, short convexity"),
 "QAI":S("HF multi-strategy","Liquid alt","Alt",[["bootstrap","bootstrap"]],0,"rentable HF beta, cash-like"),
 "DBMF":S("Managed futures","Liquid alt","Alt",[["bootstrap","bootstrap"],["boulder","boulder"]],1,"low-corr crisis diversifier"),
 "KMLM":S("Managed futures","Liquid alt","Alt",[["boulder","boulder"]],1,"trend diversifier"),
 "BALT":S("Buffered equity","Defined outcome","Structure",[["bezel","bezel"],["buckler","buckler"]],0,"symmetric beta-reduction + fee"),
 "BUFR":S("Laddered buffer","Defined outcome","Structure",[["bezel","bezel"]],0,"capped equity + fee"),
 "UPRO":S("3x S&P 500","Leveraged","Leverage",[["belligerent","belligerent"],["beaming","beaming"]],-1,"3x beta, ruin-shaped"),
 "TQQQ":S("3x Nasdaq","Leveraged","Leverage",[["belligerent","belligerent"]],-1,"3x growth, ruin-shaped"),
 "SQQQ":S("-3x Nasdaq","Leveraged","Leverage",[["bear","bear"]],-1,"inverse, structural bleed"),
}
# single stocks: (name, sector, sleeveRepo, skew, risk)
ST={
 "AAPL":("Apple","Technology","bogle",-1,"mega-cap growth"),"MSFT":("Microsoft","Technology","bogle",-1,"mega-cap growth"),
 "NVDA":("Nvidia","Technology","bogle",-1,"high-beta growth, fat tails"),"GOOGL":("Alphabet","Communication","bogle",-1,"mega-cap growth"),
 "GOOG":("Alphabet","Communication","bogle",-1,"mega-cap growth"),"AMZN":("Amazon","Discretionary","bogle",-1,"mega-cap growth"),
 "META":("Meta","Communication","bogle",-1,"mega-cap growth"),"AVGO":("Broadcom","Technology","bogle",-1,"high-beta semis"),
 "ORCL":("Oracle","Technology","bogle",-1,"large-cap tech"),"CRM":("Salesforce","Technology","bogle",-1,"growth software"),
 "ADBE":("Adobe","Technology","bogle",-1,"growth software"),"AMD":("AMD","Technology","bogle",-1,"high-beta semis"),
 "INTC":("Intel","Technology","bogle",-1,"semis, turnaround"),"CSCO":("Cisco","Technology","bogle",0,"mature tech"),
 "QCOM":("Qualcomm","Technology","bogle",-1,"semis"),"TXN":("Texas Instruments","Technology","bogle",0,"analog semis"),
 "IBM":("IBM","Technology","bogle",0,"mature tech, income"),"NOW":("ServiceNow","Technology","bogle",-1,"growth software"),
 "PLTR":("Palantir","Technology","bogle",-1,"high-beta growth, extreme multiple"),
 "NFLX":("Netflix","Communication","bogle",-1,"growth media"),"DIS":("Disney","Communication","bogle",-1,"cyclical media"),
 "TMUS":("T-Mobile","Communication","bogle",0,"telecom"),"NKE":("Nike","Discretionary","bogle",-1,"consumer cyclical"),
 "SBUX":("Starbucks","Discretionary","bogle",-1,"consumer cyclical"),"MCD":("McDonald's","Discretionary","bogle",0,"defensive consumer"),
 "HD":("Home Depot","Discretionary","brownstone",-1,"housing cyclical"),"LOW":("Lowe's","Discretionary","brownstone",-1,"housing cyclical"),
 "WMT":("Walmart","Staples","belt-tighteners",0,"defensive retail"),"COST":("Costco","Staples","belt-tighteners",0,"defensive retail, high multiple"),
 "PG":("P&G","Staples","belt-tighteners",1,"defensive staple"),"KO":("Coca-Cola","Staples","belt-tighteners",1,"defensive staple"),
 "PEP":("PepsiCo","Staples","belt-tighteners",1,"defensive staple"),"PM":("Philip Morris","Staples","belt-tighteners",0,"defensive, income"),
 "JPM":("JPMorgan","Financials","basel",-1,"bank: economy + duration"),"BAC":("Bank of America","Financials","basel",-1,"bank factor"),
 "WFC":("Wells Fargo","Financials","basel",-1,"bank factor"),"GS":("Goldman Sachs","Financials","basel",-1,"capital-markets bank"),
 "MS":("Morgan Stanley","Financials","basel",-1,"capital-markets bank"),"C":("Citigroup","Financials","basel",-1,"bank factor"),
 "BLK":("BlackRock","Financials","blackstone",-1,"asset-manager beta"),"SCHW":("Schwab","Financials","basel",-1,"broker, rate-sensitive"),
 "AXP":("Amex","Financials","basel",-1,"consumer credit"),"V":("Visa","Financials","bogle",0,"payments network"),
 "MA":("Mastercard","Financials","bogle",0,"payments network"),"BRK.B":("Berkshire","Financials","buffett",0,"quality/value conglomerate"),
 "BX":("Blackstone","Financials","blackstone",-1,"listed PE, levered pro-cyclical"),"KKR":("KKR","Financials","blackstone",-1,"listed PE"),
 "APO":("Apollo","Financials","blackstone",-1,"listed PE / credit"),
 "UNH":("UnitedHealth","Healthcare","bio",-1,"managed care"),"JNJ":("J&J","Healthcare","bio",1,"defensive large cap"),
 "LLY":("Eli Lilly","Healthcare","bio",-1,"growth pharma, high multiple"),"ABBV":("AbbVie","Healthcare","bio",0,"pharma income"),
 "MRK":("Merck","Healthcare","bio",0,"pharma"),"PFE":("Pfizer","Healthcare","bio",0,"pharma, value"),
 "TMO":("Thermo Fisher","Healthcare","bio",-1,"life-science tools"),"ABT":("Abbott","Healthcare","bio",0,"med devices"),
 "AMGN":("Amgen","Healthcare","bio",0,"biotech large cap"),"GILD":("Gilead","Healthcare","bio",0,"biotech, income"),
 "XOM":("Exxon","Energy","barrel",-1,"integrated energy"),"CVX":("Chevron","Energy","barrel",-1,"integrated energy"),
 "COP":("ConocoPhillips","Energy","barrel",-1,"E&P energy"),"SLB":("Schlumberger","Energy","barrel",-1,"oil services"),
 "OXY":("Occidental","Energy","barrel",-1,"high-beta E&P"),"CAT":("Caterpillar","Industrials","bigbrother",-1,"global cyclical"),
 "DE":("Deere","Industrials","bonfire",-1,"ag cyclical"),"BA":("Boeing","Industrials","battered",-1,"deep cyclical, idiosyncratic"),
 "GE":("GE Aerospace","Industrials","bigbrother",-1,"aerospace cyclical"),"HON":("Honeywell","Industrials","bigbrother",0,"diversified industrial"),
 "UNP":("Union Pacific","Industrials","bellwether",-1,"rail bellwether"),"UPS":("UPS","Industrials","bellwether",-1,"logistics bellwether"),
 "LMT":("Lockheed","Industrials","bulk",0,"defense, low-beta"),"RTX":("RTX","Industrials","bulk",0,"defense"),
 "TSLA":("Tesla","Discretionary","bogle",-1,"high-beta growth/EV, extreme tail"),
 "SPCX":("SpaceX","Technology","bogle",-1,"newly listed aerospace, connectivity and AI; limited trading history"),
 "F":("Ford","Discretionary","battered",-1,"auto cyclical"),
 "GM":("General Motors","Discretionary","battered",-1,"auto cyclical"),"RIVN":("Rivian","Discretionary","bogle",-1,"EV, cash-burn tail"),
 "T":("AT&T","Communication","belt-tighteners",0,"telecom income"),"VZ":("Verizon","Communication","belt-tighteners",0,"telecom income"),
}
for t,(n,sec,rep,sk,risk) in ST.items():
    U[t]=S(n,"Single stock",sec,[[rep,rep]],sk,"single-name: "+risk)

EQ=[t for t in U if U[t][1]!="Crypto" or U[t][2]!="Crypto"]  # placeholder
EQUITIES=[t for t in U if U[t][1] not in ("Crypto",) or t in ("IBIT","BITO","ETHA","COIN","MSTR","MARA","RIOT")]
CRYPTO=["BTC","ETH","SOL"]
EQUITIES=[t for t in EQUITIES if t not in CRYPTO]

def bars_eq(syms):
    out={}
    for i in range(0,len(syms),30):
        chunk=",".join(syms[i:i+30]); tok=None
        while True:
            u=f"https://data.alpaca.markets/v2/stocks/bars?symbols={urllib.parse.quote(chunk)}&timeframe=1Day&start={START}&end={END}&adjustment=all&feed=sip&limit=10000"+(f"&page_token={tok}" if tok else "")
            d=fetch(u)
            for s,b in d.get("bars",{}).items(): out.setdefault(s,{}).update({x["t"][:10]:x["c"] for x in b})
            tok=d.get("next_page_token")
            if not tok: break
        time.sleep(0.4); print(f"  ...{min(i+30,len(syms))}/{len(syms)}")
    return out
def bars_cx(syms):
    out={}
    sl="/USD,".join(syms)+"/USD"
    u=f"https://data.alpaca.markets/v1beta3/crypto/us/bars?symbols={urllib.parse.quote(sl)}&timeframe=1Day&start={START}&limit=10000"
    try:
        d=fetch(u)
        for s,b in d.get("bars",{}).items(): out[s.split("/")[0]]={x["t"][:10]:x["c"] for x in b}
    except Exception as e: print("crypto pull failed:",e)
    return out

print("pulling",len(EQUITIES),"equities +",len(CRYPTO),"crypto ...")
PX=bars_eq(EQUITIES); PX.update(bars_cx(CRYPTO))
# common date index from SPY
spd=sorted(PX["SPY"]);
def series(t):
    if t not in PX or len(PX[t])<60: return None
    d=sorted(PX[t]); px=np.array([PX[t][x] for x in d],float); return d,px
def rets(px): return px[1:]/px[:-1]-1
def align(t):
    s=series(t);
    if not s: return None
    d,px=s; dd=set(d); common=[x for x in spd if x in dd]
    if len(common)<60: return None
    m={x:PX[t][x] for x in common}; p=np.array([m[x] for x in common],float); return common,p

# factor basis (daily returns, aligned to SPY dates)
def fret(t):
    a=align(t); return (a[0],rets(a[1])) if a else None
base={}
for t in ["SPY","TLT","IEF","HYG","DBC","GLD","MTUM","VLUE","USMV","VNQ","EFA","VWO","BTC","VIXM"]:
    base[t]=fret(t)
spyd,spyr=base["SPY"]
def fac_series():
    idx={d:i for i,d in enumerate(spyd)}
    def g(t):
        if not base.get(t): return np.zeros(len(spyd))
        d,r=base[t]; out=np.zeros(len(spyd))
        for dd,rr in zip(d[ -len(r):] if len(d)>len(r) else d, r):
            if dd in idx: out[idx[dd]]=rr
        return out
    MKT=g("SPY"); return {
      "MKT":MKT,"RATES":g("TLT"),"CREDIT":g("HYG")-g("IEF"),"COMMOD":g("DBC"),"GOLD":g("GLD"),
      "MOM":g("MTUM")-MKT,"VALUE":g("VLUE")-MKT,"LOWVOL":g("USMV")-MKT,"REALEST":g("VNQ")-MKT,
      "INTL":g("EFA")-MKT,"EM":g("VWO")-MKT,"CRYPTO":g("BTC"),"VOL":g("VIXM")}
FAC=fac_series(); FKEYS=list(FAC)
Fmat=np.column_stack([FAC[k] for k in FKEYS])

def ema(x,n):
    a=2/(n+1); e=x[0]; o=[e]
    for v in x[1:]: e=a*v+(1-a)*e; o.append(e)
    return np.array(o)
def rsi(px,n=14):
    d=np.diff(px); up=np.clip(d,0,None); dn=-np.clip(d,None,0)
    ru=ema(up,n); rd=ema(dn,n); rs=ru/np.maximum(rd,1e-9); return 100-100/(1+rs[-1])
def trend_score(px):
    if len(px)<210: return 0
    e20,e50,e200=ema(px,20)[-1],ema(px,50)[-1],ema(px,200)[-1]; p=px[-1]; s=0
    s+= 1 if p>e50 else -1; s+= 1 if e50>e200 else -1
    return int(max(-2,min(2,s)))
def mom_score(px):
    if len(px)<40: return 0
    r=rsi(px); macd=ema(px,12)[-1]-ema(px,26)[-1]; sig=ema(ema(px,12)-ema(px,26),9)[-1]; s=0
    s+= 1 if r>55 else (-1 if r<45 else 0); s+= 1 if macd>sig else -1
    return int(max(-2,min(2,s)))

def reg(y):
    # per-factor CORRELATION: bounded [-1,1], comparable across factors (beta explodes on low-var spreads)
    L=min(len(y),len(Fmat)); Y=y[-L:]; sy=np.std(Y); out={}
    for i,k in enumerate(FKEYS):
        f=Fmat[-L:,i]; sf=np.std(f)
        out[k]=round(float(np.corrcoef(Y,f)[0,1]),3) if (sy>0 and sf>0) else 0.0
    return out
def beta_spy(y):
    L=min(len(y),len(Fmat)); Y=y[-L:]; mkt=Fmat[-L:,FKEYS.index("MKT")]; v=np.var(mkt)
    return round(float(np.cov(Y,mkt)[0,1]/v),2) if v>0 else 0.0

tickers={}
for t in list(EQUITIES)+CRYPTO:
    a=align(t)
    if not a: continue
    d,p=a; r=rets(p)
    # regress returns on factors (align r to spy dates)
    idx={x:i for i,x in enumerate(spyd)}; yv=np.zeros(len(spyd))
    for dd,rr in zip(d[1:],r):
        if dd in idx: yv[idx[dd]]=rr
    betas=reg(yv)
    hi=p[-252:].max() if len(p)>=252 else p.max()
    tickers[t]=dict(
        px=round(float(p[-1]),2), asof=d[-1],
        r1m=round(float(p[-1]/p[-22]-1),4) if len(p)>22 else None,
        r3m=round(float(p[-1]/p[-64]-1),4) if len(p)>64 else None,
        r1y=round(float(p[-1]/p[-253]-1),4) if len(p)>253 else None,
        vol=round(float(np.std(r[-63:])*math.sqrt(252)),4) if len(r)>63 else None,
        dd52=round(float(p[-1]/hi-1),4), rsi=round(float(rsi(p)),1),
        trend=trend_score(p), mom=mom_score(p), betaSPY=beta_spy(yv), fx=betas)

# global macro regime from ratios (risk-on count -> -2..+2)
def ratio_up(a,b,n=63):
    A=align(a); B=align(b)
    if not A or not B: return 0
    da,pa=A; db,pb=B; m=set(da)&set(db); cm=sorted(m)[-n-1:]
    if len(cm)<n: return 0
    ra=PX[a][cm[-1]]/PX[a][cm[0]]; rb=PX[b][cm[-1]]/PX[b][cm[0]]
    return 1 if ra>rb else -1
macro=sum([ratio_up("HYG","LQD"),ratio_up("SPY","TLT"),ratio_up("XLY","XLP"),ratio_up("IWM","SPY")])
macro=int(max(-2,min(2,round(macro/2))))

meta={t:dict(n=U[t][0],cls=U[t][1],sector=U[t][2],sleeve=U[t][3],skew=U[t][4],risk=U[t][5]) for t in tickers if t in U}
out=dict(asof=spd[-1], macro=macro, factors=FKEYS, meta=meta, stats=tickers,
         n=len(tickers), generated=datetime.datetime.utcnow().isoformat()+"Z")
json.dump(out, open(os.path.join(os.path.dirname(__file__),"data.json"),"w"), separators=(",",":"))
print(f"wrote data.json: {len(tickers)} tickers, asof {spd[-1]}, macro {macro}")
