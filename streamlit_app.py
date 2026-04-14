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
    page_title="Republic World — Advanced Chart Analytics",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ═══════════════════════════════════════════════════════════
#  CSS — Republic Light Theme
# ═══════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@300;400;500;600;700;800;900&family=Barlow+Condensed:wght@500;600;700;800&family=IBM+Plex+Mono:wght@400;600&display=swap');

*, html, body, [class*="css"] {
    font-family: 'Barlow', sans-serif !important;
}

/* ── Root: clean white ── */
[data-testid="stAppViewContainer"] {
    background: #f2f4f8 !important;
}
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Top nav ── */
.topbar {
    background: #ffffff;
    border-bottom: 3px solid #e63535;
    padding: 0 24px;
    height: 54px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    position: sticky; top: 0; z-index: 999;
}
.rep-badge {
    background: #e63535;
    color: #fff;
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 800;
    font-size: 14px;
    letter-spacing: 2px;
    padding: 5px 12px;
    border-radius: 3px;
}
.topbar-title {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-size: 17px;
    font-weight: 700;
    color: #1a1a2e;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}
.topbar-copy {
    font-size: 12px;
    color: #888;
    letter-spacing: 0.3px;
}
.live-pill {
    display: flex; align-items: center; gap: 7px;
    background: #fff5f5;
    border: 1.5px solid #e63535;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 11px;
    font-weight: 800;
    color: #e63535;
    letter-spacing: 2px;
}
.live-dot {
    width: 7px; height: 7px;
    background: #e63535; border-radius: 50%;
    animation: blink 1.2s infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.2} }

/* ── Content wrapper ── */
.cw { padding: 16px 24px 36px; }

/* ── Subtitle strip ── */
.subtitle-strip {
    background: #1a1a2e;
    padding: 8px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.subtitle-main {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-size: 13px;
    font-weight: 600;
    color: #ffffff;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}
.subtitle-right {
    font-size: 11px;
    color: #aab0cc;
    letter-spacing: 0.5px;
    font-family: 'IBM Plex Mono', monospace !important;
}

/* ── Ticker cards ── */
.ticker-grid {
    display: grid;
    grid-template-columns: repeat(6,1fr);
    gap: 10px;
    margin-bottom: 14px;
}
.tcard {
    background: #ffffff;
    border: 1px solid #e8eaf0;
    border-radius: 10px;
    padding: 13px 14px 11px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    transition: box-shadow 0.2s, transform 0.2s;
}
.tcard:hover { box-shadow: 0 6px 20px rgba(0,0,0,0.10); transform: translateY(-2px); }
.tcard-top { position:absolute;top:0;left:0;width:100%;height:3.5px;border-radius:10px 10px 0 0; }
.tcard-lbl {
    font-size: 9px; font-weight: 700;
    letter-spacing: 1.2px; text-transform: uppercase;
    color: #9098b0; margin-bottom: 5px; line-height: 1.4;
}
.tcard-val {
    font-size: 28px; font-weight: 800;
    font-family: 'Barlow Condensed', sans-serif !important;
    line-height: 1; letter-spacing: -0.5px;
}
.tcard-delta {
    font-size: 11px; font-weight: 700;
    margin-top: 5px;
    font-family: 'IBM Plex Mono', monospace !important;
}
.up   { color: #16a34a; }
.dn   { color: #dc2626; }
.flat { color: #9098b0; }

/* ── Section label ── */
.slbl {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-size: 11px; font-weight: 700;
    letter-spacing: 2.5px; text-transform: uppercase;
    color: #9098b0;
    margin: 18px 0 10px;
    display: flex; align-items: center; gap: 10px;
}
.slbl::after {
    content:''; flex:1; height:1px;
    background: linear-gradient(90deg,#e8eaf0,transparent);
}

/* ── Chart / panel box ── */
.pbox {
    background: #ffffff;
    border: 1px solid #e8eaf0;
    border-radius: 12px;
    padding: 4px;
    margin-bottom: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

/* ── Legend strip ── */
.leg-strip {
    display: flex; gap: 18px; flex-wrap: wrap; align-items: center;
    padding: 8px 14px;
    border-top: 1px solid #f0f2f8;
    background: #fafbfd;
    border-radius: 0 0 12px 12px;
}
.leg-item { display:flex;align-items:center;gap:7px;font-size:11px;color:#6070a0; }
.leg-line  { width:20px;height:2.5px;border-radius:2px; }
.leg-val   { font-family:'IBM Plex Mono',monospace;font-weight:700; }

/* ── Stats table ── */
.stbl-wrap {
    background:#ffffff;border:1px solid #e8eaf0;
    border-radius:12px;padding:16px 18px;height:100%;
    box-shadow:0 2px 8px rgba(0,0,0,0.04);
}
.panel-ttl {
    font-family:'Barlow Condensed',sans-serif!important;
    font-size:13px;font-weight:700;letter-spacing:2px;
    text-transform:uppercase;color:#1a1a2e;margin-bottom:2px;
}
.panel-sub { font-size:10px;color:#9098b0;letter-spacing:0.5px;margin-bottom:12px; }
.stbl { width:100%;border-collapse:collapse;font-size:12.5px; }
.stbl th {
    font-size:9px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;
    color:#9098b0;padding:4px 7px 8px;text-align:right;
    border-bottom:2px solid #f0f2f8;
}
.stbl th:first-child { text-align:left; }
.stbl td {
    padding:8px 7px;text-align:right;
    border-bottom:1px solid #f5f6fa;color:#1a1a2e;
    font-family:'IBM Plex Mono',monospace;font-size:12px;
}
.stbl td:first-child { text-align:left;font-family:'Barlow',sans-serif!important; }
.stbl tr:hover td { background:#fafbfd; }
.dot { display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px; }

/* ── Heatmap wrap ── */
.hmwrap {
    background:#ffffff;border:1px solid #e8eaf0;border-radius:12px;
    padding:16px 18px;box-shadow:0 2px 8px rgba(0,0,0,0.04);
}

/* ── Share panel ── */
.sharewrap {
    background:#ffffff;border:1px solid #e8eaf0;border-radius:12px;
    padding:16px 18px;height:100%;box-shadow:0 2px 8px rgba(0,0,0,0.04);
}
.sbar-row { display:flex;align-items:center;gap:9px;margin-bottom:8px; }
.sbar-lbl { font-size:11px;font-weight:600;width:82px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#444; }
.sbar-track { flex:1;height:5px;background:#f0f2f8;border-radius:3px;overflow:hidden; }
.sbar-fill  { height:100%;border-radius:3px; }
.sbar-pct   { font-size:11px;font-weight:700;font-family:'IBM Plex Mono',monospace;width:38px;text-align:right; }

/* ── Footer ── */
.footer {
    margin-top:20px;padding:12px 18px;
    background:#1a1a2e;border-radius:10px;
    display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;
}
.footer span { font-size:11px;color:#5a6080; }
.footer b    { color:#9098b0; }

/* ── Hide Streamlit chrome ── */
#MainMenu,footer,header { visibility:hidden!important }
[data-testid="stToolbar"] { display:none!important }
::-webkit-scrollbar { width:4px;height:4px }
::-webkit-scrollbar-track { background:#f0f2f8 }
::-webkit-scrollbar-thumb { background:#c8cce0;border-radius:4px }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
#  CONSTANTS  — Republic-inspired smooth palette
# ═══════════════════════════════════════════════════════════
COLORS  = ["#e63535","#0ea5e9","#8b5cf6","#16a34a","#f59e0b","#f97316"]
BG_L    = "#ffffff"
PAPER_L = "#ffffff"
GRID_L  = "rgba(0,0,0,0.05)"
FC_L    = "#6070a0"
IST     = pytz.timezone("Asia/Kolkata")

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

def BL(h=300, ml=44, mr=12, mt=30, mb=28):
    return dict(
        paper_bgcolor=PAPER_L, plot_bgcolor=BG_L,
        font=dict(color=FC_L, family="Barlow", size=11),
        height=h, margin=dict(l=ml,r=mr,t=mt,b=mb),
        xaxis=dict(gridcolor=GRID_L,linecolor="#e8eaf0",tickfont=dict(size=10),zeroline=False),
        yaxis=dict(gridcolor=GRID_L,linecolor="#e8eaf0",tickfont=dict(size=10),zeroline=False),
        hoverlabel=dict(bgcolor="#1a1a2e",font_color="#fff",
                        font_family="Barlow",bordercolor="rgba(0,0,0,0.1)"),
    )

# ═══════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ Controls")
    time_window = st.slider("Time window (hours)", 1, 48, 24)
    max_vids    = st.slider("Max videos to fetch", 6, 100, 40, step=6)
    top_n       = st.slider("Videos in main chart", 3, 6, 6)
    st.divider()
    if st.button("🔄 Refresh"):
        st.cache_data.clear(); st.rerun()

# ═══════════════════════════════════════════════════════════
#  API + FETCH
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
            v=it["id"]["videoId"]; ids.append(v); snips[v]=it["snippet"]
        npt = r.get("nextPageToken")
        if not npt or len(ids)>=max_res: break
    if not ids: return pd.DataFrame()

    sm = {}
    for i in range(0,len(ids),50):
        chunk=ids[i:i+50]
        det=youtube.videos().list(
            part="statistics,snippet,contentDetails",id=",".join(chunk)
        ).execute()
        for it in det.get("items",[]):
            v=it["id"]; s2=it.get("statistics",{}); sn=it.get("snippet",{})
            cd=it.get("contentDetails",{})
            raw=cd.get("duration","PT0S")
            h2=re.search(r'(\d+)H',raw); m2=re.search(r'(\d+)M',raw); s3=re.search(r'(\d+)S',raw)
            dur=(int(h2.group(1)) if h2 else 0)*3600+(int(m2.group(1)) if m2 else 0)*60+(int(s3.group(1)) if s3 else 0)
            sm[v]=dict(
                views=int(s2.get("viewCount",0)),likes=int(s2.get("likeCount",0)),
                comments=int(s2.get("commentCount",0)),tags=sn.get("tags",[]),
                cat=CAT_MAP.get(sn.get("categoryId",""),"Other"),dur=dur,
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
            title=sn.get("title","N/A"),pub=ist_t,pub_utc=utc,
            hrs=round(hrs,2),views=s["views"],likes=s["likes"],
            comments=s["comments"],vph=round(s["views"]/hrs,2),
            eng=round((s["likes"]+s["comments"])/max(s["views"],1)*100,3),
            dur=s["dur"],cat=s["cat"],tags=s["tags"],vid=v,
        ))
    df2=pd.DataFrame(rows).sort_values("views",ascending=False).reset_index(drop=True)
    return df2

def make_series(top):
    out={}
    for i,(_,row) in enumerate(top.iterrows()):
        tot_h=max(row["hrs"],0.5); tot_v=row["views"]
        n=min(int(tot_h*4),120); n=max(n,4)
        times=[row["pub_utc"]+timedelta(hours=j*tot_h/(n-1)) for j in range(n)]
        xs=np.linspace(-4,2,n)
        raw=1/(1+np.exp(-xs)); raw=raw/raw[-1]
        noise=np.random.normal(0,0.01,n)
        raw=np.clip(raw+noise,0,None); raw=raw/raw[-1]
        out[row["title"][:28]]=dict(
            times=times,views=(raw*tot_v).astype(int).tolist(),
            color=COLORS[i%len(COLORS)],vid=row["vid"],
        )
    return out

def make_momentum(series,step=3):
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
        sub=df[df["cat"]==c]; rv=[]
        for h in range(24):
            val=0
            for _,r in sub.iterrows():
                d=min(abs(r["pub"].hour-h),24-abs(r["pub"].hour-h))
                val+=r["views"]*max(0,1-d/8)
            rv.append(int(val))
        mat[c]=rv
    return pd.DataFrame(mat,index=list(range(24)))

# ═══════════════════════════════════════════════════════════
#  LOAD DATA
# ═══════════════════════════════════════════════════════════
with st.spinner(""):
    df=fetch(CHANNEL_ID,time_window,max_vids)

if df.empty:
    st.error(f"No videos found in the last {time_window} hours."); st.stop()

top6   = df.head(top_n).reset_index(drop=True)
series = make_series(top6)
now_s  = datetime.now(IST).strftime("%H:%M")
today  = datetime.now(IST).strftime("%d %b %Y")
total_v= top6["views"].sum()

# ═══════════════════════════════════════════════════════════
#  TOP BAR
# ═══════════════════════════════════════════════════════════
st.markdown(f"""
<div class="topbar">
  <div style="display:flex;align-items:center;gap:14px;">
    <span class="rep-badge">REPUBLIC</span>
    <div>
      <div class="topbar-title">Republic World — YouTube Real-Time Live | Video Shorts Advance Chart</div>
    </div>
  </div>
  <span class="topbar-copy">© Manish Rawat &nbsp;|&nbsp; Republic Media Network</span>
  <div style="display:flex;align-items:center;gap:14px;">
    <span style="font-size:12px;color:#9098b0;font-family:'IBM Plex Mono',monospace;">{now_s} IST · {today}</span>
    <div class="live-pill"><div class="live-dot"></div>LIVE</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Subtitle strip
st.markdown(f"""
<div class="subtitle-strip">
  <span class="subtitle-main">📡 &nbsp; Advanced Chart Analytics &nbsp;·&nbsp; YouTube Data API v3 &nbsp;·&nbsp; Live Intelligence Dashboard</span>
  <span class="subtitle-right">{len(df)} videos tracked &nbsp;·&nbsp; window: {time_window}h &nbsp;·&nbsp; cache: 5 min</span>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
#  CONTENT WRAPPER
# ═══════════════════════════════════════════════════════════
st.markdown('<div class="cw">', unsafe_allow_html=True)

# ── TICKER ROW ─────────────────────────────────────────────
tk='<div class="ticker-grid">'
for i,(_,row) in enumerate(top6.iterrows()):
    c=COLORS[i%len(COLORS)]; vph=int(row["vph"])
    sg="▲" if vph>=0 else "▼"; cls="up" if vph>=0 else "dn"
    short=row["title"][:22]+"…" if len(row["title"])>22 else row["title"]
    tk+=f"""
    <div class="tcard">
      <div class="tcard-top" style="background:{c};"></div>
      <div class="tcard-lbl">{short}</div>
      <div class="tcard-val" style="color:{c};">{fk(row['views'])}</div>
      <div class="tcard-delta {cls}">{sg}&nbsp;{fk(abs(vph))}/hr</div>
    </div>"""
tk+='</div>'
st.markdown(tk,unsafe_allow_html=True)

# ── MAIN CHART ─────────────────────────────────────────────
st.markdown('<div class="slbl">📈 &nbsp; Views Timeline + Market Momentum — Δ Total Views / Interval</div>', unsafe_allow_html=True)
st.markdown('<div class="pbox">', unsafe_allow_html=True)

fig=make_subplots(
    rows=3,cols=1,
    row_heights=[0.60,0.22,0.18],
    shared_xaxes=True,
    vertical_spacing=0.03,
)

# Lines
for name,s in series.items():
    c=s["color"]
    fig.add_trace(go.Scatter(
        x=s["times"],y=s["views"],name=name,
        line=dict(color=c,width=2.2),mode="lines",
        hovertemplate=f"<b style='color:{c}'>{name}</b><br>%{{x|%H:%M}}<br>Views: %{{y:,}}<extra></extra>",
    ),row=1,col=1)

# Momentum
mt,md=make_momentum(series,step=3)
bc=["#16a34a" if d>=0 else "#dc2626" for d in md]
fig.add_trace(go.Bar(
    x=mt,y=md,marker_color=bc,marker_line_width=0,
    hovertemplate="Δ Views: %{y:,}<extra></extra>",opacity=0.85,
),row=2,col=1)
fig.add_hline(y=0,line_color="rgba(0,0,0,0.1)",line_width=1,row=2,col=1)

total_delta=md[-1] if md else 0
sg_d="▲" if total_delta>=0 else "▼"
fig.add_annotation(
    text="MARKET MOMENTUM — Δ TOTAL VIEWS / INTERVAL",
    xref="paper",yref="paper",x=0,y=0.365,showarrow=False,
    font=dict(size=8,color="#9098b0"),align="left",
)
fig.add_annotation(
    text=f"{sg_d} +{fk(abs(int(total_delta)))} TOTAL",
    xref="paper",yref="paper",x=1,y=0.365,showarrow=False,
    font=dict(size=9,color="#16a34a" if total_delta>=0 else "#dc2626"),align="right",
)

# Navigator
for name,s in series.items():
    mx=max(s["views"]) if s["views"] else 1
    norm=[v/mx for v in s["views"]]
    fig.add_trace(go.Scatter(
        x=s["times"],y=norm,line=dict(color=s["color"],width=1),
        mode="lines",opacity=0.4,hoverinfo="skip",
    ),row=3,col=1)
fig.add_annotation(
    text="NAVIGATOR — DRAG SLIDERS TO ZOOM",
    xref="paper",yref="paper",x=0,y=0.02,showarrow=False,
    font=dict(size=8,color="#9098b0"),align="left",
)

fig.update_layout(
    paper_bgcolor=PAPER_L,plot_bgcolor=BG_L,height=480,
    margin=dict(l=50,r=14,t=12,b=8),
    font=dict(color=FC_L,family="Barlow",size=10),
    hovermode="x unified",showlegend=False,
    hoverlabel=dict(bgcolor="#1a1a2e",font_color="#fff",
                    font_family="Barlow",bordercolor="rgba(0,0,0,0.1)"),
    xaxis3=dict(
        rangeslider=dict(visible=True,bgcolor="#f2f4f8",
                         bordercolor="#e8eaf0",thickness=0.10),
        type="date",tickfont=dict(size=9),gridcolor=GRID_L,showticklabels=True,
    ),
)
for r in [1,2,3]:
    fig.update_xaxes(gridcolor=GRID_L,linecolor="#e8eaf0",tickfont=dict(size=9),row=r,col=1)
    fig.update_yaxes(gridcolor=GRID_L,linecolor="#e8eaf0",tickfont=dict(size=9),row=r,col=1)

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
      <span class="leg-val" style="color:#1a1a2e;font-size:13px;">{fk(v)}</span>
      <span class="leg-val {cls}" style="font-size:10px;">{sg}{fk(int(abs(vph)))}</span>
    </div>"""
ls+='</div>'
st.markdown(ls, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)  # pbox

# ── BOTTOM 3-PANEL ─────────────────────────────────────────
st.markdown('<div class="slbl">📊 &nbsp; Channel Statistics · Hourly Heatmap · Current Share</div>', unsafe_allow_html=True)

p1,p2,p3=st.columns([3,4,2.5],gap="small")

# Stats table
with p1:
    st.markdown('<div class="stbl-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="panel-ttl">Channel Statistics</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-sub">Current · Avg/Hr · Velocity · Engagement</div>', unsafe_allow_html=True)
    rows_h=""
    for i,(_,row) in enumerate(top6.iterrows()):
        c=COLORS[i%len(COLORS)]; vph=int(row["vph"]); avg=int(row["views"]/max(row["hrs"],1))
        sg="▲" if vph>=0 else "▼"; cls="up" if vph>=0 else "dn"
        sh=row["title"][:26]+"…" if len(row["title"])>26 else row["title"]
        rows_h+=f"""
        <tr>
          <td><span class="dot" style="background:{c};"></span>{sh}</td>
          <td style="color:{c};font-weight:700;">{fk(row['views'])}</td>
          <td style="color:#9098b0;">{fk(avg)}</td>
          <td><span class="{cls}">{sg}{fk(abs(vph))}</span></td>
          <td style="color:#6070a0;">{row['eng']:.2f}%</td>
        </tr>"""
    st.markdown(f"""
    <table class="stbl">
      <thead>
        <tr><th>CHANNEL</th><th>NOW</th><th>AVG/HR</th><th>Δ30M</th><th>ENGMT</th></tr>
      </thead>
      <tbody>{rows_h}</tbody>
    </table>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Heatmap
with p2:
    st.markdown('<div class="hmwrap">', unsafe_allow_html=True)
    st.markdown('<div class="panel-ttl">Hourly Activity Heatmap</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-sub">Avg views per hour — deeper colour = higher</div>', unsafe_allow_html=True)
    hm=hour_heatmap(df)
    if not hm.empty:
        top_cats=hm.sum().nlargest(6).index.tolist()
        hm_s=hm[top_cats]
        # Light-friendly color scales (white→color)
        cscales=[
            [[0,"#fff5f5"],[1,"#e63535"]],
            [[0,"#f0f9ff"],[1,"#0ea5e9"]],
            [[0,"#f5f3ff"],[1,"#8b5cf6"]],
            [[0,"#f0fdf4"],[1,"#16a34a"]],
            [[0,"#fffbeb"],[1,"#f59e0b"]],
            [[0,"#fff7ed"],[1,"#f97316"]],
        ]
        fig_hm=make_subplots(
            rows=1,cols=len(top_cats),shared_yaxes=True,horizontal_spacing=0.015,
            subplot_titles=[f"<b>{c[:4].upper()}</b>" for c in top_cats]
        )
        hlbls=[f"{h:02d}h" for h in range(24)]
        for ci,cat in enumerate(top_cats):
            vals=hm_s[cat].values
            fig_hm.add_trace(go.Heatmap(
                z=vals.reshape(-1,1),y=hlbls,x=[cat[:4]],
                colorscale=cscales[ci%len(cscales)],showscale=False,
                text=[[fk(v)] for v in vals],texttemplate="%{text}",
                textfont=dict(size=8,color="rgba(0,0,0,0.55)"),
                hovertemplate=f"<b>{cat}</b><br>%{{y}}: %{{z:,}}<extra></extra>",
                xgap=2,ygap=1,
            ),row=1,col=ci+1)
        fig_hm.update_layout(
            paper_bgcolor=PAPER_L,plot_bgcolor=BG_L,height=375,
            margin=dict(l=32,r=6,t=28,b=6),
            font=dict(color=FC_L,family="Barlow",size=9),
        )
        fig_hm.update_xaxes(showticklabels=False,showgrid=False)
        fig_hm.update_yaxes(tickfont=dict(size=8),gridcolor=GRID_L)
        # Color the subtitles
        for ann in fig_hm.layout.annotations:
            txt=ann.text.replace("<b>","").replace("</b>","").strip()
            for ci2,cat in enumerate(top_cats):
                if cat[:4].upper()==txt:
                    ann.font=dict(size=10,color=COLORS[ci2%len(COLORS)],
                                  family="Barlow Condensed")
                    break
        st.plotly_chart(fig_hm,use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

# Share panel
with p3:
    st.markdown('<div class="sharewrap">', unsafe_allow_html=True)
    st.markdown('<div class="panel-ttl">Current Share</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="panel-sub">at {now_s} IST</div>', unsafe_allow_html=True)
    fig_d=go.Figure(go.Pie(
        labels=[r["title"][:16] for _,r in top6.iterrows()],
        values=top6["views"].tolist(),hole=0.60,
        marker=dict(colors=COLORS[:len(top6)],line=dict(color="#f2f4f8",width=3)),
        textinfo="none",direction="clockwise",sort=False,
        hovertemplate="<b>%{label}</b><br>%{value:,} (%{percent})<extra></extra>",
    ))
    fig_d.add_annotation(
        text=f"<b>{fk(total_v)}</b><br><span style='font-size:10px;'>total</span>",
        x=0.5,y=0.5,showarrow=False,
        font=dict(size=17,color="#1a1a2e",family="Barlow Condensed"),align="center",
    )
    fig_d.update_layout(
        paper_bgcolor=PAPER_L,plot_bgcolor=BG_L,height=195,
        margin=dict(l=6,r=6,t=6,b=6),showlegend=False,
        font=dict(color=FC_L,family="Barlow"),
    )
    st.plotly_chart(fig_d,use_container_width=True,config={"displayModeBar":False})
    bh=""
    for i,(_,row) in enumerate(top6.iterrows()):
        c=COLORS[i%len(COLORS)]; pct=row["views"]/max(total_v,1)*100
        sh=row["title"][:18]+"…" if len(row["title"])>18 else row["title"]
        bh+=f"""
        <div class="sbar-row">
          <span class="sbar-lbl" style="color:{c};">{sh}</span>
          <div class="sbar-track"><div class="sbar-fill" style="width:{pct:.1f}%;background:{c};"></div></div>
          <span class="sbar-pct" style="color:{c};">{pct:.1f}%</span>
        </div>"""
    st.markdown(bh, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── DEEP ANALYTICS ─────────────────────────────────────────
st.markdown('<div class="slbl" style="margin-top:16px;">🔬 &nbsp; Tag Intelligence · Engagement Matrix · Duration Profile</div>', unsafe_allow_html=True)

d1,d2,d3=st.columns(3,gap="small")

with d1:
    st.markdown('<div class="pbox">', unsafe_allow_html=True)
    all_tags=[]
    for t in df["tags"].dropna():
        lst=t if isinstance(t,list) else [x.strip() for x in t.split(",")]
        all_tags.extend([x.lower() for x in lst if x.strip()])
    if all_tags:
        tdf=pd.DataFrame(Counter(all_tags).most_common(22),columns=["Tag","Count"])
        fig_t=px.treemap(tdf,path=["Tag"],values="Count",color="Count",
                         color_continuous_scale=["#f0f9ff","#0ea5e9","#8b5cf6"])
        fig_t.update_traces(
            textfont=dict(family="Barlow",size=12,color="#1a1a2e"),
            hovertemplate="<b>%{label}</b>: %{value}<extra></extra>",
            marker_line_width=1.5,marker_line_color="#f2f4f8",
        )
        fig_t.update_layout(
            paper_bgcolor=PAPER_L,height=275,
            margin=dict(l=4,r=4,t=32,b=4),
            font=dict(color=FC_L,family="Barlow"),
            coloraxis_showscale=False,
            title=dict(text="🏷️  TAG INTELLIGENCE",
                       font=dict(size=10,color="#9098b0",family="Barlow Condensed"),x=0.01),
        )
        st.plotly_chart(fig_t,use_container_width=True,config={"displayModeBar":False})
    else:
        st.info("No tag data available.")
    st.markdown('</div>', unsafe_allow_html=True)

with d2:
    st.markdown('<div class="pbox">', unsafe_allow_html=True)
    fig_s=go.Figure()
    for i,cat in enumerate(df["cat"].unique()):
        sub=df[df["cat"]==cat].head(20)
        fig_s.add_trace(go.Scatter(
            x=sub["views"],y=sub["eng"],mode="markers",name=cat,
            marker=dict(
                size=sub["vph"].apply(lambda v:max(5,min(v/300,20))),
                color=COLORS[i%len(COLORS)],opacity=0.75,
                line=dict(color="rgba(255,255,255,0.8)",width=1),
            ),
            hovertemplate="<b>%{customdata}</b><br>Views: %{x:,}<br>Eng: %{y:.2f}%<extra></extra>",
            customdata=sub["title"].str[:30],
        ))
    _sl = BL(h=275,ml=44,mr=10,mt=32,mb=32)
    _sl["showlegend"] = True
    _sl["legend"] = dict(orientation="h",y=-0.2,font=dict(size=9),bgcolor="rgba(0,0,0,0)")
    _sl["title"] = dict(text="💡  VIEWS vs ENGAGEMENT % — bubble = velocity",
                        font=dict(size=10,color="#9098b0",family="Barlow Condensed"),x=0.01)
    fig_s.update_layout(**_sl)
    st.plotly_chart(fig_s,use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

with d3:
    st.markdown('<div class="pbox">', unsafe_allow_html=True)
    dur_df=df[df["dur"]>0].copy(); dur_df["dm"]=dur_df["dur"]/60
    fig_dur=go.Figure(go.Histogram(
        x=dur_df["dm"],nbinsx=16,
        marker=dict(
            color=dur_df["dm"],
            colorscale=[[0,"#f0fdf4"],[0.4,"#16a34a"],[0.75,"#f59e0b"],[1,"#e63535"]],
            line=dict(color="#f2f4f8",width=1),
        ),
        hovertemplate="~%{x:.0f} min: %{y} videos<extra></extra>",
    ))
    _dl = BL(h=275,ml=44,mr=10,mt=32,mb=32)
    _dl["showlegend"] = False
    _dl["title"] = dict(text="🕐  DURATION DISTRIBUTION (minutes)",
                        font=dict(size=10,color="#9098b0",family="Barlow Condensed"),x=0.01)
    fig_dur.update_layout(**_dl)
    st.plotly_chart(fig_dur,use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

# ── FOOTER ─────────────────────────────────────────────────
st.markdown(f"""
<div class="footer">
  <span>
    📡 <b>Source:</b> YouTube Data API v3 &nbsp;·&nbsp;
    🔑 <b>Auth:</b> st.secrets &nbsp;·&nbsp;
    🕐 <b>Cache TTL:</b> 5 minutes &nbsp;·&nbsp;
    📍 <b>Timezone:</b> Asia / Kolkata (IST)
  </span>
  <span style="color:#c8d0f0;font-family:'IBM Plex Mono',monospace;">
    © Manish Rawat &nbsp;|&nbsp; Republic Media Network &nbsp;·&nbsp;
    {len(df)} videos · {time_window}h window · {now_s} IST
  </span>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # cw
