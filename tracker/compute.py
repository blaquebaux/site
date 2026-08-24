#!/usr/bin/python3
# Compute SIMULATED YTD-2026 equity curves ($100k base) for the capstones + balsamic, vs SPY & DIA.
# Simulated = each sleeve's rule run on ETF data, gross of costs. NOT a live track record.
import os, json, urllib.request, datetime
import numpy as np
H={"APCA-API-KEY-ID":os.environ["ALPACA_KEY_ID"],"APCA-API-SECRET-KEY":os.environ["ALPACA_SECRET_KEY"]}
_END=(datetime.date.today()-datetime.timedelta(days=1)).strftime("%Y-%m-%d")
def load(sym,start="2024-06-01",end=None):
    end=end or _END
    u=(f"https://data.alpaca.markets/v2/stocks/bars?symbols={sym}&timeframe=1Day&start={start}&end={end}"
       f"&adjustment=all&feed=sip&limit=10000"); d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=40))
    b=d.get("bars",{}).get(sym,[]); return {x["t"][:10]:x["c"] for x in b}
SPINE=["SPY","IEF","GLD","DBC","DBA"]; TREND=["SPY","IEF","GLD","DBC"]; TAIL=["GLD","TLT"]
PE=["BX","KKR","APO","CG","ARES","BAM"]; NEAR=["USMV","VNQ","EEM"]; MF=["SPY","IEF","GLD","DBC","TLT","UUP","EEM","HYG","VNQ"]
BM=["SPY","DIA"]; HF=["QAI","DBMF","BRK.B"]; ALL=sorted(set(SPINE+TREND+TAIL+PE+NEAR+MF+["KSA","QQQ"]+BM+HF))
D={s:load(s) for s in ALL}; dates=sorted(set.intersection(*[set(D[s]) for s in ALL]))
P={s:np.array([D[s][d] for d in dates],float) for s in ALL}; R={s:P[s][1:]/P[s][:-1]-1 for s in ALL}
DT=dates[1:]; T=len(R["SPY"]); VW,REB=60,21
def _invvol(syms):
    M=np.vstack([R[s] for s in syms]); out=np.zeros(T); w=np.ones(len(syms))/len(syms)
    for t in range(VW,T):
        if (t-VW)%REB==0:
            v=np.array([M[i,t-VW:t].std() for i in range(len(syms))]); inv=np.divide(1.,v,out=np.zeros_like(v),where=v>0)
            w=inv/inv.sum() if inv.sum()>0 else np.ones(len(syms))/len(syms)
        out[t]=float(w@M[:,t])
    return out
def _trend(syms,ls=False):
    lv={s:np.cumprod(1+R[s]) for s in syms}; out=np.zeros(T); w=np.zeros(len(syms))
    for t in range(252,T):
        if (t-252)%REB==0:
            sig=np.array([(1. if (lv[s][t]/lv[s][t-231]-1)>0 else(-1. if ls else 0.)) for s in syms]); w=sig/(len(syms) if ls else max(sig.sum(),1))
        out[t]=float(sum(w[i]*R[syms[i]][t] for i in range(len(syms))))
    return out
KEEP={"spine":_invvol(SPINE),"trend":_trend(TREND),"tail":_invvol(TAIL),"gulf":R["KSA"],"growth":R["QQQ"],"PE":np.mean(np.vstack([R[s] for s in PE]),axis=0)}
KM=np.vstack(list(KEEP.values())); KMx=np.vstack(list(KEEP.values())+[R[s] for s in NEAR])
def run(M,rule):
    k,Tn=M.shape; out=np.zeros(Tn); w=np.ones(k)/k
    for t in range(252,Tn):
        if (t-252)%REB==0:
            if rule=="rp": v=M[:,t-VW:t].std(axis=1); inv=np.divide(1.,v,out=np.zeros_like(v),where=v>0); s=inv.sum(); w=inv/s if s>0 else np.ones(k)/k
            elif rule=="mv":
                C=np.cov(M[:,t-VW:t])+1e-6*np.eye(k)
                try: w=np.clip(np.linalg.solve(C,np.ones(k)),0,None); s=w.sum(); w=w/s if s>0 else np.ones(k)/k
                except np.linalg.LinAlgError: w=np.ones(k)/k
            elif rule=="eq": w=np.ones(k)/k
        out[t]=float(w@M[:,t])
    return out[252:]
bt=run(KM,"rp"); bril=run(KM,"mv"); belv=run(KM,"eq"); brig=run(KMx,"rp")
bear=_trend(["SPY"]); bas=0.85*bt+0.15*np.where(bear[252:]==0.,-1.*R["SPY"][252:],0.)
sat=_trend(MF,ls=True)[252:]; vc,vs=bt[-60:].std(),sat[-60:].std(); a=(0.30/0.70)*(vc/vs)
bals=bt+a*sat; boss=1.5*bt
DTc=DT[252:]
streams={"breakthrough":bt,"brilliant":bril,"bossy":boss,"believer":belv,"brigade":brig,"bastion":bas,"balsamic":bals}
labels={"breakthrough":"Breakthrough — risk parity","brilliant":"Brilliant — optimizer","bossy":"Bossy — 1.5× levered",
        "believer":"Believer — buy & hold","brigade":"Brigade — curated breadth","bastion":"Bastion — with insurance","balsamic":"Balsamic — core + trend"}
# slice YTD 2026, rebase to 100k
ix=[i for i,d in enumerate(DTc) if d>="2026-01-01"]
if not ix: raise SystemExit("no 2026 data")
i0=ix[0]; ydates=[DTc[i] for i in ix]
def equity(r):
    seg=r[i0:i0+len(ix)]; return list(np.round(100000*np.cumprod(1+seg),2))
series={}
for k,r in streams.items(): series[k]={"label":labels[k],"kind":"capstone","equity":equity(r)}
for b,lab in [("SPY","S&P 500 (SPY)"),("DIA","Dow Jones (DIA)")]:
    rb=R[b][252:]; series[b]={"label":lab,"kind":"benchmark","equity":equity(rb)}
for b,lab in [("QAI","Hedge funds (broad)"),("DBMF","Managed futures / CTA"),("BRK.B","Berkshire (Buffett)")]:
    rb=R[b][252:]; series[b]={"label":lab,"kind":"hedgefund","equity":equity(rb)}
out={"asof":dates[-1],"start":ydates[0],"dates":ydates,"series":series}
open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"performance.json"),"w").write(json.dumps(out))
# quick console summary
print(f"YTD 2026 ({ydates[0]} → {ydates[-1]}, {len(ydates)} days) — $100k base, SIMULATED:")
for k in list(streams)+["SPY","DIA","QAI","DBMF","BRK.B"]:
    e=series[k]["equity"]; ret=(e[-1]/100000-1)*100; print(f"  {k:<13} ${e[-1]:>11,.0f}   {ret:+.1f}%")
