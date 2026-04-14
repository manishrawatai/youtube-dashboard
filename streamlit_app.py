import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pytz, re
import numpy as np
from collections import Counter

# ═══════════════════════════════════════════════════════════
#  PAGE CONFIG
# ═══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Advanced Chart Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ═══════════════════════════════════════════════════════════
#  MASTER CSS
# ═══════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap');

*, html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif !important;
}
[data-testid="stAppViewContainer"] { background:#0b0e1a !important; }
.block-container { padding:0 !important; max-width:100% !important; }

/* Top Bar */
.topbar {
    background:linear-gradient(90deg,#0f1120,#131628);
    border-bottom:1px solid rgba(255,255,255,0.07);
    padding:0 28px; height:52px;
    display:flex; align-items:center; justify-content:space-between;
}
.brand-badge {
    background:#e63535; color:#fff;
    font-weight:800; font-size:12px; letter-spacing:2px;
    padding:4px 10px; border-radius:4px;
}
.live-badge {
    display:flex; align-items:center; gap:8px;
    background:rgba(0,230,118,0.1); border:1px solid rgba(0,230,118,0.3);
    border-radius:20px; padding:4px 14px;
    font-size:11px; font-weight:700; color:#00e676; letter-spacing:1.5px;
}
.live-dot {
    width:7px; height:7px; background:#00e676; border-radius:50%;
    animation:pulse 1.5s infinite;
}
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.4;transform:scale(1.4)} }

/* Content */
.cw { padding:18px 28px 36px; }

/* Ticker */
.ticker-grid {
    display:grid; grid-template-columns:repeat(6,1fr); gap:10px; margin-bottom:16px;
}
.tcard {
    background:#111427; border:1px solid rgba(255,255,255,0.06);
    border-radius:12px; padding:12px 14px; position:relative;
    overflow:hidden; transition:transform 0.2s,border-color 0.25s;
}
.tcard:hover { transform:translateY(-2px); }
.tcard-accent { position:absolute;top:0;left:0;width:100%;height:3px;border-radius:12px 12px 0 0; }
.tcard-lbl { font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#5a6080;margin-bottom:5px; }
.tcard-val { font-size:25px;font-weight:700;font-family:'IBM Plex Mono',monospace!important;line-height:1; }
.tcard-delta { font-size:11px;font-weight:600;margin-top:5px;font-family:'IBM Plex Mono',monospace!important; }
.up{color:#00e676} .dn{color:#ff4b4b} .flat{color:#5a6080}

/* Section label */
.slbl {
    font-size:10px;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;
    color:#3a4060;margin:20px 0 10px;display:flex;align-items:center;gap:10px;
}
.slbl::after{content:'';flex:1;height:1px;background:linear-gradient(90deg,rgba(255,255,255,0.06),transparent);}

/* Chart box */
.cbox { background:#111427;border:1px solid rgba(255,255,255,0.06);border-radius:14px;padding:4px;margin-bottom:14px; }

/* Legend strip */
.leg-strip {
    display:flex;gap:16px;flex-wrap:wrap;align-items:center;
    padding:8px 14px;border-top:1px solid rgba(255,255,255,0.04);
}
.leg-item { display:flex;align-items:center;gap:7px;font-size:11px;color:#8890b0; }
.leg-line { width:20px;height:2px;border-radius:1px; }
.leg-val { font-family:'IBM Plex Mono',monospace;font-weight:700; }

/* Stats table */
.stbl-wrap {
    background:#111427;border:1px solid rgba(255,255,255,0.06);
    border-radius:14px;padding:18px 18px;height:100%;
}
.panel-ttl { font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#c8ccff;margin-bottom:3px; }
.panel-sub { font-size:10px;color:#3a4060;letter-spacing:0.5px;margin-bottom:14px; }
.stbl { width:100%;border-collapse:collapse;font-size:12px; }
.stbl th {
    color:#3a4060;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;
    padding:4px 7px 9px;text-align:right;border-bottom:1px solid rgba(255,255,255,0.05);
}
.stbl th:first-child{text-align:left;}
.stbl td {
    padding:8px 7px;text-align:right;border-bottom:1px solid rgba(255,255,255,0.03);
    color:#c8ccff;font-family:'IBM Plex Mono',monospace;font-size:12px;
}
.stbl td:first-child{text-align:left;font-family:'IBM Plex Sans',sans-serif!important;font-size:12px;}
.stbl tr:hover td{background:rgba(255,255,255,0.02);}
.dot { display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:7px; }

/* Heatmap wrap */
.hmwrap {
    background:#111427;border:1px solid rgba(255,255,255,0.06);
    border-radius:14px;padding:18px 18px;
}

/* Share panel */
.sharewrap {
    background:#111427;border:1px solid rgba(255,255,255,0.06);
    border-radius:14px;padding:18px 18px;height:100%;
}
.sbar-row { display:flex;align-items:center;gap:9px;margin-bottom:8px; }
.sbar-lbl { font-size:11px;font-weight:600;width:78px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis; }
.sbar-track { flex:1;height:5px;background:rgba(255,255,255,0.05);border-radius:3px;overflow:hidden; }
.sbar-fill { height:100%;border-radius:3px; }
.sbar-pct { font-size:11px;font-weight:700;font-family:'IBM Plex Mono',monospace;width:36px;text-align:right; }

/* Footer */
.footer {
    margin-top:24px;padding:14px 20px;
    background:#111427;border:1px solid rgba(255,255,255,0.05);
    border-radius:12px;display:flex;justify-content:space-between;
    align-items:center;flex-wrap:wrap;gap:8px;
}
.footer span { font-size:11px;color:#3a4060; }
.footer b { color:#5a6080; }

#MainMenu,footer,header{visibility:hidden!important}
[data-testid="stToolbar"]{display:none!important}
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:#0b0e1a}
::-webkit-scrollbar-thumb{background:#2a2e4a;border-radius:4px}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════
COLORS = ["#FF4B4B","#00C4FF","#9B59FF","#00E676","#FFB300","#FF6B35"]
BG     = "#111427"
PAPER  = "#111427"
GRID   = "rgba(255,255,255,0.04)"
FC     = "#8890b0"
IST    = pytz.timezone("Asia/Kolkata")

CAT_MAP = {
    "1":"Film","2":"Autos","10":"Music","15":"Pets","17":"Sports",
    "19":"Travel","20":"Gaming","22":"Blogs","23":"Comedy",
    "24":"Entertainment","25":"News","26":"Style","27":"Education",
    "28":"Science","29":"Nonprofits",
}

def fk(n):
    if n>=1_000_000: return f"{n/1_000_000:.1f}M"
    if n>=1_000:     return f"{n/1_000:.1f}k"
    return str(int(n))

def BL(h=320, ml=40, mr=12, mt=28, mb=24):
    return dict(
        paper_bgcolor=PAPER, plot_bgcolor=BG,
        font=dict(color=FC, family="IBM Plex Sans", size=10),
        height=h, margin=dict(l=ml,r=mr,t=mt,b=mb),
        xaxis=dict(gridcolor=GRID,linecolor="rgba(0,0,0,0)",tickfont=dict(size=9),zeroline=False),
        yaxis=dict(gridcolor=GRID,linecolor="rgba(0,0,0,0)",tickfont=dict(size=9),zeroline=False),
        hoverlabel=dict(bgcolor="#1a1e35",font_color="#fff",
                        font_family="IBM Plex Sans",bordercolor="rgba(255,255,255,0.1)"),
        showlegend=False,
    )

# ═══════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️  Controls")
    time_window = st.slider("Time window (hours)", 1, 48, 24)
    max_vids    = st.slider("Max videos to fetch", 6, 100, 40, step=6)
    top_n       = st.slider("Videos in main chart", 3, 6, 6)
    st.divider()
    if st.button("🔄 Refresh"):
        st.cache_data.clear(); st.rerun()

# ═══════════════════════════════════════════════════════════
#  DATA FETCH
# ═══════════════════════════════════════════════════════════
API_KEY    = st.secrets["YOUTUBE_API_KEY"]
CHANNEL_ID = st.secrets["YOUTUBE_CHANNEL_ID"]
youtube    = build("youtube","v3",developerKey=API_KEY)

@st.cache_data(ttl=300)
def fetch(channel_id, hours, max_res):
    now   = datetime.utcnow()
    after = (now-timedelta(hours=hours)).isoformat("T")+"Z"
    ids, snips = [], {}
    npt = None
    while True:
        r = youtube.search().list(
            part="snippet",channelId=channel_id,
            maxResults=min(max_res,50),order="date",
            publishedAfter=after,type="video",pageToken=npt
        ).execute()
        for it in r.get("items",[]):
            v = it["id"]["videoId"]; ids.append(v); snips[v]=it["snippet"]
        npt = r.get("nextPageToken")
        if not npt or len(ids)>=max_res: break
    if not ids: return pd.DataFrame()

    sm = {}
    for i in range(0,len(ids),50):
        chunk = ids[i:i+50]
        det = youtube.videos().list(
            part="statistics,snippet,contentDetails",id=",".join(chunk)
        ).execute()
        for it in det.get("items",[]):
            v=it["id"]; st2=it.get("statistics",{}); sn=it.get("snippet",{})
            cd=it.get("contentDetails",{})
            raw=cd.get("duration","PT0S")
            h2=re.search(r'(\d+)H',raw); m2=re.search(r'(\d+)M',raw); s2=re.search(r'(\d+)S',raw)
            dur=(int(h2.group(1)) if h2 else 0)*3600+(int(m2.group(1)) if m2 else 0)*60+(int(s2.group(1)) if s2 else 0)
            sm[v]=dict(
                views=int(st2.get("viewCount",0)),
                likes=int(st2.get("likeCount",0)),
                comments=int(st2.get("commentCount",0)),
                tags=sn.get("tags",[]),
                cat=CAT_MAP.get(sn.get("categoryId",""),"Other"),
                dur=dur,
            )
    rows=[]
    for v in ids:
        if v not in sm: continue
        s=sm[v]; sn=snips.get(v,{})
        utc=datetime.strptime(sn.get("publishedAt","2000-01-01T00:00:00Z"),
                              "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
        ist_t=utc.astimezone(IST)
        hrs=max((datetime.now(pytz.utc)-utc).total_seconds()/3600,0.1)
        rows.append(dict(
            title=sn.get("title","N/A"), pub=ist_t, pub_utc=utc,
            hrs=round(hrs,2), views=s["views"], likes=s["likes"],
            comments=s["comments"], vph=round(s["views"]/hrs,2),
            eng=round((s["likes"]+s["comments"])/max(s["views"],1)*100,3),
            dur=s["dur"], cat=s["cat"], tags=s["tags"], vid=v,
        ))
    df2=pd.DataFrame(rows).sort_values("views",ascending=False).reset_index(drop=True)
    return df2

def make_series(top):
    """Logistic growth curves for top videos."""
    out={}
    for i,(_, row) in enumerate(top.iterrows()):
        tot_h=max(row["hrs"],0.5); tot_v=row["views"]
        n=min(int(tot_h*4),120); n=max(n,4)
        times=[row["pub_utc"]+timedelta(hours=j*tot_h/(n-1)) for j in range(n)]
        xs=np.linspace(-4,2,n)
        raw=1/(1+np.exp(-xs)); raw=raw/raw[-1]
        noise=np.random.normal(0,0.01,n)
        raw=np.clip(raw+noise,0,None); raw=raw/raw[-1]
        out[row["title"][:28]]=dict(
            times=times, views=(raw*tot_v).astype(int).tolist(),
            color=COLORS[i%len(COLORS)], vid=row["vid"],
        )
    return out

def make_momentum(series, step=3):
    if not series: return [],[]
    ref=next(iter(series.values())); n=len(ref["times"])
    times,deltas=[],[]
    prev=0
    for i in range(0,n,step):
        t=ref["times"][i]
        tot=sum(s["views"][min(i,len(s["views"])-1)] for s in series.values())
        deltas.append(tot-prev); prev=tot; times.append(t)
    return times[1:],deltas[1:]

def hour_heatmap(df):
    cats=df["cat"].unique(); mat={}
    for c in cats:
        sub=df[df["cat"]==c]; row_vals=[]
        for h in range(24):
            val=0
            for _,r in sub.iterrows():
                d=min(abs(r["pub"].hour-h),24-abs(r["pub"].hour-h))
                val+=r["views"]*max(0,1-d/8)
            row_vals.append(int(val))
        mat[c]=row_vals
    return pd.DataFrame(mat,index=list(range(24)))

# ═══════════════════════════════════════════════════════════
#  LOAD
# ═══════════════════════════════════════════════════════════
with st.spinner(""):
    df = fetch(CHANNEL_ID, time_window, max_vids)

if df.empty:
    st.error(f"No videos in last {time_window}h."); st.stop()

top6   = df.head(top_n).reset_index(drop=True)
series = make_series(top6)
now_s  = datetime.now(IST).strftime("%H:%M")
total_v= top6["views"].sum()

# ═══════════════════════════════════════════════════════════
#  TOP BAR
# ═══════════════════════════════════════════════════════════
st.markdown(f"""
<div class="topbar">
  <div style="display:flex;align-items:center;gap:14px;">
    <span class="brand-badge">YT</span>
    <span style="font-size:15px;font-weight:600;color:#e0e4ff;letter-spacing:0.5px;">Advanced Chart Analytics</span>
  </div>
  <span style="font-size:12px;color:#5a6080;letter-spacing:0.5px;">© Analytics Dashboard &nbsp;|&nbsp; YouTube Data API v3</span>
  <div style="display:flex;align-items:center;gap:14px;">
    <span style="font-size:12px;color:#3a4060;font-family:'IBM Plex Mono',monospace;">{now_s} IST</span>
    <div class="live-badge"><div class="live-dot"></div>LIVE</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
#  CONTENT
# ═══════════════════════════════════════════════════════════
st.markdown('<div class="cw">', unsafe_allow_html=True)

# ── TICKER ROW ─────────────────────────────────────────────
tk = '<div class="ticker-grid">'
for i,(_,row) in enumerate(top6.iterrows()):
    c=COLORS[i%len(COLORS)]; vph=int(row["vph"])
    sign="▲" if vph>=0 else "▼"; cls="up" if vph>=0 else "dn"
    short=row["title"][:20]+"…" if len(row["title"])>20 else row["title"]
    tk+=f"""
    <div class="tcard">
      <div class="tcard-accent" style="background:{c};"></div>
      <div class="tcard-lbl">{short}</div>
      <div class="tcard-val" style="color:{c};">{fk(row['views'])}</div>
      <div class="tcard-delta {cls}">{sign}&nbsp;{fk(vph)}/hr</div>
    </div>"""
tk+='</div>'
st.markdown(tk, unsafe_allow_html=True)

# ── MAIN CHART (line + momentum + navigator) ───────────────
st.markdown('<div class="slbl">📈 &nbsp; Views Timeline + Market Momentum — Δ Total Views / Interval</div>', unsafe_allow_html=True)
st.markdown('<div class="cbox">', unsafe_allow_html=True)

fig = make_subplots(
    rows=3, cols=1,
    row_heights=[0.60,0.22,0.18],
    shared_xaxes=True,
    vertical_spacing=0.03,
)

# Main lines
for name,s in series.items():
    c=s["color"]
    fig.add_trace(go.Scatter(
        x=s["times"], y=s["views"], name=name,
        line=dict(color=c,width=2.2), mode="lines",
        hovertemplate=f"<b style='color:{c}'>{name}</b><br>%{{x|%H:%M}}<br>Views: %{{y:,}}<extra></extra>",
    ),row=1,col=1)

# Momentum bars
mt,md=make_momentum(series,step=3)
bc=["#00E676" if d>=0 else "#FF4B4B" for d in md]
fig.add_trace(go.Bar(
    x=mt,y=md,marker_color=bc,marker_line_width=0,
    hovertemplate="Δ Views: %{y:,}<extra></extra>",opacity=0.85,
),row=2,col=1)
fig.add_hline(y=0,line_color="rgba(255,255,255,0.08)",line_width=1,row=2,col=1)
fig.add_annotation(
    text="MARKET MOMENTUM — Δ TOTAL VIEWS / INTERVAL",
    xref="paper",yref="paper",x=0,y=0.365,showarrow=False,
    font=dict(size=8,color="#3a4060"),align="left",
)
total_delta = md[-1] if md else 0
sign_d = "▲" if total_delta>=0 else "▼"
fig.add_annotation(
    text=f"{sign_d} {fk(abs(int(total_delta)))} TOTAL",
    xref="paper",yref="paper",x=1,y=0.365,showarrow=False,
    font=dict(size=9,color="#00E676" if total_delta>=0 else "#FF4B4B"),align="right",
)

# Navigator
for name,s in series.items():
    mx=max(s["views"]) if s["views"] else 1
    norm=[v/mx for v in s["views"]]
    fig.add_trace(go.Scatter(
        x=s["times"],y=norm,
        line=dict(color=s["color"],width=1),
        mode="lines",opacity=0.45,hoverinfo="skip",
    ),row=3,col=1)
fig.add_annotation(
    text="NAVIGATOR — DRAG SLIDERS TO ZOOM",
    xref="paper",yref="paper",x=0,y=0.02,showarrow=False,
    font=dict(size=8,color="#3a4060"),align="left",
)

fig.update_layout(
    paper_bgcolor=PAPER,plot_bgcolor=BG,height=480,
    margin=dict(l=50,r=14,t=12,b=8),
    font=dict(color=FC,family="IBM Plex Sans",size=10),
    hovermode="x unified",showlegend=False,
    hoverlabel=dict(bgcolor="#1a1e35",font_color="#fff",
                    font_family="IBM Plex Sans",bordercolor="rgba(255,255,255,0.1)"),
    xaxis3=dict(
        rangeslider=dict(visible=True,bgcolor="#0b0e1a",
                         bordercolor="rgba(255,255,255,0.06)",thickness=0.10),
        type="date",tickfont=dict(size=9),gridcolor=GRID,
        showticklabels=True,
    ),
)
for r in [1,2,3]:
    fig.update_xaxes(gridcolor=GRID,linecolor="rgba(0,0,0,0)",tickfont=dict(size=9),row=r,col=1)
    fig.update_yaxes(gridcolor=GRID,linecolor="rgba(0,0,0,0)",tickfont=dict(size=9),row=r,col=1)

st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

# Legend strip
ls='<div class="leg-strip">'
for i,(name,s) in enumerate(series.items()):
    c=s["color"]
    vid_rows=[r for _,r in top6.iterrows() if r["vid"]==s["vid"]]
    v=vid_rows[0]["views"] if vid_rows else 0
    vph=vid_rows[0]["vph"] if vid_rows else 0
    sg="▲" if vph>=0 else "▼"; cls="up" if vph>=0 else "dn"
    ls+=f"""
    <div class="leg-item">
      <div class="leg-line" style="background:{c};"></div>
      <span style="color:{c};font-weight:700;">{name[:22]}</span>
      <span class="leg-val" style="color:#fff;font-size:13px;">{fk(v)}</span>
      <span class="leg-val {cls}" style="font-size:10px;">{sg}{fk(int(abs(vph)))}</span>
    </div>"""
ls+='</div>'
st.markdown(ls+'\n</div>',unsafe_allow_html=True)  # closes cbox

# ── BOTTOM 3-PANEL ─────────────────────────────────────────
st.markdown('<div class="slbl">📊 &nbsp; Channel Statistics · Hourly Heatmap · Current Share</div>', unsafe_allow_html=True)

c1,c2,c3=st.columns([3,4,2.5],gap="small")

# Stats table
with c1:
    st.markdown('<div class="stbl-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="panel-ttl">CHANNEL STATISTICS</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-sub">Current · Avg/Hr · Velocity · Engagement</div>', unsafe_allow_html=True)
    rows_h=""
    for i,(_,row) in enumerate(top6.iterrows()):
        c=COLORS[i%len(COLORS)]; vph=int(row["vph"]); avg=int(row["views"]/max(row["hrs"],1))
        sg="▲" if vph>=0 else "▼"; cls="up" if vph>=0 else "dn"
        sh=row["title"][:24]+"…" if len(row["title"])>24 else row["title"]
        rows_h+=f"""
        <tr>
          <td><span class="dot" style="background:{c};"></span>{sh}</td>
          <td style="color:{c};font-weight:700;">{fk(row['views'])}</td>
          <td style="color:#5a6080;">{fk(avg)}</td>
          <td><span class="{cls}">{sg}{fk(abs(vph))}</span></td>
          <td style="color:#8890b0;">{row['eng']:.2f}%</td>
        </tr>"""
    st.markdown(f"""
    <table class="stbl">
      <thead>
        <tr><th>VIDEO</th><th>NOW</th><th>AVG/HR</th><th>Δ V/HR</th><th>ENGMT</th></tr>
      </thead>
      <tbody>{rows_h}</tbody>
    </table>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Heatmap
with c2:
    st.markdown('<div class="hmwrap">', unsafe_allow_html=True)
    st.markdown('<div class="panel-ttl">HOURLY ACTIVITY HEATMAP</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-sub">Avg views per hour — deeper colour = higher</div>', unsafe_allow_html=True)
    hm=hour_heatmap(df)
    if not hm.empty:
        top_cats=hm.sum().nlargest(6).index.tolist()
        hm_s=hm[top_cats]
        cscales=[
            [[0,BG],[1,"#FF4B4B"]],
            [[0,BG],[1,"#00C4FF"]],
            [[0,BG],[1,"#9B59FF"]],
            [[0,BG],[1,"#00E676"]],
            [[0,BG],[1,"#FFB300"]],
            [[0,BG],[1,"#FF6B35"]],
        ]
        fig_hm=make_subplots(
            rows=1,cols=len(top_cats),shared_yaxes=True,horizontal_spacing=0.01,
            subplot_titles=[f"<b>{c[:4].upper()}</b>" for c in top_cats]
        )
        hlbls=[f"{h:02d}h" for h in range(24)]
        for ci,cat in enumerate(top_cats):
            vals=hm_s[cat].values
            fig_hm.add_trace(go.Heatmap(
                z=vals.reshape(-1,1),y=hlbls,x=[cat[:4]],
                colorscale=cscales[ci%len(cscales)],showscale=False,
                text=[[fk(v)] for v in vals],texttemplate="%{text}",
                textfont=dict(size=8,color="rgba(255,255,255,0.65)"),
                hovertemplate=f"<b>{cat}</b><br>%{{y}}: %{{z:,}}<extra></extra>",
                xgap=2,ygap=1,
            ),row=1,col=ci+1)
        fig_hm.update_layout(
            paper_bgcolor=PAPER,plot_bgcolor=BG,height=370,
            margin=dict(l=30,r=6,t=28,b=6),
            font=dict(color=FC,family="IBM Plex Sans",size=9),
        )
        fig_hm.update_xaxes(showticklabels=False,showgrid=False)
        fig_hm.update_yaxes(tickfont=dict(size=8),gridcolor=GRID)
        for ann in fig_hm.layout.annotations:
            ann.font=dict(size=10,color=COLORS[top_cats.index(ann.text[3:-4].lower().strip())
                                              if ann.text[3:-4].lower().strip() in
                                              [c[:4].lower() for c in top_cats] else 0])
        st.plotly_chart(fig_hm,use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

# Share panel
with c3:
    st.markdown('<div class="sharewrap">', unsafe_allow_html=True)
    st.markdown('<div class="panel-ttl">CURRENT SHARE</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="panel-sub">at {now_s}</div>', unsafe_allow_html=True)
    fig_d=go.Figure(go.Pie(
        labels=[r["title"][:16] for _,r in top6.iterrows()],
        values=top6["views"].tolist(),hole=0.60,
        marker=dict(colors=COLORS[:len(top6)],line=dict(color=BG,width=3)),
        textinfo="none",direction="clockwise",sort=False,
        hovertemplate="<b>%{label}</b><br>%{value:,} (%{percent})<extra></extra>",
    ))
    fig_d.add_annotation(
        text=f"<b>{fk(total_v)}</b><br><span>total</span>",
        x=0.5,y=0.5,showarrow=False,
        font=dict(size=15,color="#fff",family="IBM Plex Mono"),align="center",
    )
    fig_d.update_layout(
        paper_bgcolor=PAPER,plot_bgcolor=BG,height=190,
        margin=dict(l=6,r=6,t=6,b=6),showlegend=False,
        font=dict(color=FC,family="IBM Plex Sans"),
    )
    st.plotly_chart(fig_d,use_container_width=True,config={"displayModeBar":False})
    # Bars
    bh=""
    for i,(_,row) in enumerate(top6.iterrows()):
        c=COLORS[i%len(COLORS)]; pct=row["views"]/max(total_v,1)*100
        sh=row["title"][:17]+"…" if len(row["title"])>17 else row["title"]
        bh+=f"""
        <div class="sbar-row">
          <span class="sbar-lbl" style="color:{c};">{sh}</span>
          <div class="sbar-track"><div class="sbar-fill" style="width:{pct:.1f}%;background:{c};"></div></div>
          <span class="sbar-pct" style="color:{c};">{pct:.1f}%</span>
        </div>"""
    st.markdown(bh, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── DEEP ANALYTICS ROW ─────────────────────────────────────
st.markdown('<div class="slbl" style="margin-top:20px;">🔬 &nbsp; Tag Intelligence · Engagement Matrix · Duration Profile</div>', unsafe_allow_html=True)

d1,d2,d3=st.columns(3,gap="small")

with d1:
    st.markdown('<div class="cbox">', unsafe_allow_html=True)
    all_tags=[]
    for t in df["tags"].dropna():
        lst=t if isinstance(t,list) else [x.strip() for x in t.split(",")]
        all_tags.extend([x.lower() for x in lst if x.strip()])
    if all_tags:
        tdf=pd.DataFrame(Counter(all_tags).most_common(22),columns=["Tag","Count"])
        fig_t=px.treemap(tdf,path=["Tag"],values="Count",color="Count",
                         color_continuous_scale=["#0b0e1a","#9B59FF","#00C4FF"])
        fig_t.update_traces(textfont=dict(family="IBM Plex Sans",size=12),
                            hovertemplate="<b>%{label}</b>: %{value}<extra></extra>",
                            marker_line_width=1.5,marker_line_color=BG)
        fig_t.update_layout(
            paper_bgcolor=PAPER,height=270,
            margin=dict(l=4,r=4,t=30,b=4),
            font=dict(color=FC,family="IBM Plex Sans"),
            coloraxis_showscale=False,
            title=dict(text="🏷️  TAG INTELLIGENCE",font=dict(size=9,color="#3a4060"),x=0.01),
        )
        st.plotly_chart(fig_t,use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

with d2:
    st.markdown('<div class="cbox">', unsafe_allow_html=True)
    fig_s=go.Figure()
    for i,cat in enumerate(df["cat"].unique()):
        sub=df[df["cat"]==cat].head(20)
        fig_s.add_trace(go.Scatter(
            x=sub["views"],y=sub["eng"],mode="markers",name=cat,
            marker=dict(
                size=sub["vph"].apply(lambda v:max(5,min(v/300,20))),
                color=COLORS[i%len(COLORS)],opacity=0.8,
                line=dict(color="rgba(255,255,255,0.08)",width=0.5),
            ),
            hovertemplate="<b>%{customdata}</b><br>Views: %{x:,}<br>Eng: %{y:.2f}%<extra></extra>",
            customdata=sub["title"].str[:28],
        ))
    fig_s.update_layout(
        **BL(h=270,ml=40,mr=10,mt=30,mb=28),
        title=dict(text="💡  VIEWS vs ENGAGEMENT % — bubble = velocity",font=dict(size=9,color="#3a4060"),x=0.01),
        legend=dict(orientation="h",y=-0.18,font=dict(size=9),bgcolor="rgba(0,0,0,0)"),
        showlegend=True,
    )
    st.plotly_chart(fig_s,use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

with d3:
    st.markdown('<div class="cbox">', unsafe_allow_html=True)
    dur_df=df[df["dur"]>0].copy(); dur_df["dm"]=dur_df["dur"]/60
    fig_dur=go.Figure(go.Histogram(
        x=dur_df["dm"],nbinsx=16,
        marker=dict(
            color=dur_df["dm"],
            colorscale=[[0,BG],[0.35,"#FF4B4B"],[0.7,"#FFB300"],[1,"#00E676"]],
            line=dict(color=BG,width=1),
        ),
        hovertemplate="~%{x:.0f} min: %{y} videos<extra></extra>",
    ))
    fig_dur.update_layout(
        **BL(h=270,ml=40,mr=10,mt=30,mb=28),
        title=dict(text="🕐  DURATION DISTRIBUTION (minutes)",font=dict(size=9,color="#3a4060"),x=0.01),
    )
    st.plotly_chart(fig_dur,use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

# ── FOOTER ─────────────────────────────────────────────────
st.markdown(f"""
<div class="footer">
  <span>
    📡 <b>Source:</b> YouTube Data API v3 &nbsp;·&nbsp;
    🔑 <b>Auth:</b> st.secrets &nbsp;·&nbsp;
    🕐 <b>Cache:</b> 5 min TTL &nbsp;·&nbsp;
    📍 <b>TZ:</b> Asia / Kolkata (IST)
  </span>
  <span style="font-family:'IBM Plex Mono',monospace;">
    {len(df)} videos &nbsp;·&nbsp; window: {time_window}h &nbsp;·&nbsp; refreshed {now_s} IST
  </span>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # cw
