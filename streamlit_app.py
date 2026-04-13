import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pytz
import os
import re
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="YouTube Analytics Pro",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────
# CUSTOM CSS – Dark Cinematic Theme
# ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0a0a0f;
    color: #e8e8f0;
}

h1, h2, h3, .stMetricLabel, .stMetricValue {
    font-family: 'Syne', sans-serif !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #12121e 0%, #0d0d1a 100%);
    border-right: 1px solid #1e1e35;
}

/* Cards / Metric blocks */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #13131f 0%, #1a1a2e 100%);
    border: 1px solid #2a2a45;
    border-radius: 14px;
    padding: 18px 22px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4);
    transition: transform 0.2s, box-shadow 0.2s;
}

[data-testid="metric-container"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(91,91,255,0.15);
}

/* Step badges */
.step-badge {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    background: linear-gradient(90deg, #5b5bff22, transparent);
    border-left: 3px solid #5b5bff;
    padding: 10px 18px;
    border-radius: 0 10px 10px 0;
    margin-bottom: 8px;
    font-family: 'Syne', sans-serif;
    font-weight: 600;
    font-size: 15px;
    letter-spacing: 0.5px;
}

.step-num {
    background: #5b5bff;
    color: #fff;
    width: 24px; height: 24px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 800;
    flex-shrink: 0;
}

/* Section headers */
.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 20px;
    font-weight: 700;
    color: #a0a0ff;
    border-bottom: 1px solid #2a2a45;
    padding-bottom: 8px;
    margin-bottom: 18px;
    letter-spacing: 1px;
    text-transform: uppercase;
}

/* Tag pills */
.tag-pill {
    display: inline-block;
    background: #1e1e35;
    border: 1px solid #3a3a60;
    color: #c8c8ff;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 12px;
    margin: 2px;
}

/* Info box */
.info-box {
    background: #13131f;
    border: 1px solid #2a2a45;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
}

/* Divider */
hr { border-color: #2a2a45; }

/* DataFrame */
[data-testid="stDataFrame"] {
    border: 1px solid #2a2a45;
    border-radius: 10px;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# INIT
# ──────────────────────────────────────────────
API_KEY    = os.getenv("YOUTUBE_API_KEY", "YOUR_API_KEY_HERE")
CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID", "UCwqusr8YDwM-3mEYTDeJHzw")
youtube    = build("youtube", "v3", developerKey=API_KEY)

# ──────────────────────────────────────────────
# SIDEBAR – Controls + Steps
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Dashboard Controls")
    time_window = st.slider("⏱️ Time Window (hours)", 1, 48, 12)
    max_results = st.slider("🎯 Max Videos", 10, 200, 50, step=10)
    st.divider()

    st.markdown("## 📋 How It Works")
    for num, step in enumerate([
        "Authenticates via YouTube Data API v3",
        "Searches channel for videos in time window",
        "Batch-fetches statistics (views, likes, comments)",
        "Enriches with tags, category & region data",
        "Calculates velocity metrics (Views/Hour)",
        "Extracts keywords from titles + tags",
        "Renders charts, KPIs & breakdowns"
    ], 1):
        st.markdown(
            f'<div class="step-badge"><span class="step-num">{num}</span>{step}</div>',
            unsafe_allow_html=True
        )

    st.divider()
    st.markdown("**🔌 Source:** YouTube Data API v3")
    st.markdown("**🕐 Cache TTL:** 5 minutes")
    st.markdown("**📍 Timezone:** Asia/Kolkata (IST)")
    st.markdown(f"**📅 Report as of:** {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d %b %Y, %H:%M IST')}")

# ──────────────────────────────────────────────
# CATEGORY MAP
# ──────────────────────────────────────────────
CATEGORY_MAP = {
    "1": "Film & Animation", "2": "Autos & Vehicles", "10": "Music",
    "15": "Pets & Animals", "17": "Sports", "18": "Short Movies",
    "19": "Travel & Events", "20": "Gaming", "21": "Videoblogging",
    "22": "People & Blogs", "23": "Comedy", "24": "Entertainment",
    "25": "News & Politics", "26": "Howto & Style", "27": "Education",
    "28": "Science & Technology", "29": "Nonprofits & Activism",
}

# ──────────────────────────────────────────────
# DATA FETCH
# ──────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_data(channel_id: str, hours: int, max_res: int):
    now           = datetime.utcnow()
    published_after = (now - timedelta(hours=hours)).isoformat("T") + "Z"
    ist           = pytz.timezone("Asia/Kolkata")

    # ── Step 1: Search ──────────────────────────
    video_ids, snippets = [], {}
    next_page = None
    while True:
        resp = youtube.search().list(
            part="snippet", channelId=channel_id,
            maxResults=min(max_res, 50), order="date",
            publishedAfter=published_after, type="video",
            pageToken=next_page
        ).execute()
        for item in resp.get("items", []):
            vid = item["id"]["videoId"]
            video_ids.append(vid)
            snippets[vid] = item["snippet"]
        next_page = resp.get("nextPageToken")
        if not next_page or len(video_ids) >= max_res:
            break

    if not video_ids:
        return pd.DataFrame()

    # ── Step 2: Stats + Details ─────────────────
    stats_map = {}
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i+50]
        details = youtube.videos().list(
            part="statistics,snippet,contentDetails,topicDetails,recordingDetails",
            id=",".join(chunk)
        ).execute()
        for item in details.get("items", []):
            vid   = item["id"]
            stats = item.get("statistics", {})
            snip  = item.get("snippet", {})
            cd    = item.get("contentDetails", {})
            td    = item.get("topicDetails", {})
            rd    = item.get("recordingDetails", {})

            # parse duration ISO-8601  PT#H#M#S
            raw_dur = cd.get("duration", "PT0S")
            h = re.search(r'(\d+)H', raw_dur); m = re.search(r'(\d+)M', raw_dur); s = re.search(r'(\d+)S', raw_dur)
            dur_sec = (int(h.group(1)) if h else 0)*3600 + (int(m.group(1)) if m else 0)*60 + (int(s.group(1)) if s else 0)

            stats_map[vid] = {
                "views":        int(stats.get("viewCount",    0)),
                "likes":        int(stats.get("likeCount",    0)),
                "comments":     int(stats.get("commentCount", 0)),
                "tags":         snip.get("tags", []),
                "category_id":  snip.get("categoryId", "N/A"),
                "default_lang": snip.get("defaultAudioLanguage", snip.get("defaultLanguage", "N/A")),
                "description":  snip.get("description", "")[:200],
                "duration_sec": dur_sec,
                "topic_cats":   td.get("topicCategories", []),
                "location":     rd.get("locationDescription", "Not Specified"),
            }

    # ── Step 3: Build DataFrame ─────────────────
    rows = []
    for vid in video_ids:
        if vid not in stats_map:
            continue
        s   = stats_map[vid]
        snip = snippets.get(vid, {})
        utc_t = datetime.strptime(snip.get("publishedAt","2000-01-01T00:00:00Z"), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
        ist_t = utc_t.astimezone(ist)
        hrs   = max((datetime.now(pytz.utc) - utc_t).total_seconds() / 3600, 0.1)
        cat   = CATEGORY_MAP.get(s["category_id"], s["category_id"])
        dur_m = round(s["duration_sec"] / 60, 1)
        engagement = round((s["likes"] + s["comments"]) / max(s["views"], 1) * 100, 2)

        rows.append({
            "Title":          snip.get("title", "N/A"),
            "Published (IST)":ist_t,
            "Hours Ago":      round(hrs, 2),
            "Views":          s["views"],
            "Likes":          s["likes"],
            "Comments":       s["comments"],
            "Views/Hour":     round(s["views"] / hrs, 2),
            "Engagement %":   engagement,
            "Duration (min)": dur_m,
            "Category":       cat,
            "Language":       s["default_lang"],
            "Location":       s["location"],
            "Tags":           ", ".join(s["tags"][:8]),
            "Tag Count":      len(s["tags"]),
            "Description":    s["description"],
            "Topic URLs":     " | ".join([t.split("/")[-1].replace("_", " ") for t in s["topic_cats"][:3]]),
            "URL":            f"https://youtube.com/watch?v={vid}",
            "Video ID":       vid,
        })

    df = pd.DataFrame(rows).sort_values("Published (IST)", ascending=False)
    return df

# ──────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────
st.markdown("""
<h1 style='font-family:Syne;font-size:36px;font-weight:800;
   background:linear-gradient(90deg,#a0a0ff,#ff80bf);
   -webkit-background-clip:text;-webkit-text-fill-color:transparent;
   margin-bottom:2px;'>
  📺 YouTube Analytics Pro
</h1>
<p style='color:#6666aa;font-size:14px;margin-top:0;'>
  Real-time channel intelligence · Views · Engagement · Keywords · Trends
</p>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# LOAD
# ──────────────────────────────────────────────
with st.spinner("🔄 Fetching data from YouTube API..."):
    df = fetch_data(CHANNEL_ID, time_window, max_results)

if df.empty:
    st.warning(f"⚠️  No videos found in the last **{time_window} hours**.")
    st.stop()

# ──────────────────────────────────────────────
# TOP KPIs
# ──────────────────────────────────────────────
st.markdown('<div class="section-title">📊 Key Performance Indicators</div>', unsafe_allow_html=True)

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("📹 Videos",       len(df))
k2.metric("👀 Total Views",  f"{df['Views'].sum():,}")
k3.metric("👍 Total Likes",  f"{df['Likes'].sum():,}")
k4.metric("💬 Comments",     f"{df['Comments'].sum():,}")
k5.metric("⚡ Avg Views/Hr", f"{df['Views/Hour'].mean():,.1f}")
k6.metric("💡 Avg Engmt%",   f"{df['Engagement %'].mean():.2f}%")

st.divider()

# ──────────────────────────────────────────────
# CHARTS – Row 1: Views Timeline + Views/Hour
# ──────────────────────────────────────────────
st.markdown('<div class="section-title">📈 Performance Over Time</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)

with c1:
    fig = px.area(
        df.sort_values("Published (IST)"),
        x="Published (IST)", y="Views",
        title="📅 Views Over Upload Time",
        color_discrete_sequence=["#5b5bff"],
        template="plotly_dark",
        hover_data=["Title","Likes","Comments"]
    )
    fig.update_traces(fill="tozeroy", line_color="#5b5bff",
                      fillcolor="rgba(91,91,255,0.15)")
    fig.update_layout(paper_bgcolor="#0d0d1a", plot_bgcolor="#0d0d1a",
                      font_color="#c8c8ff", title_font_size=14)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    top_viral = df.nlargest(15, "Views/Hour")
    fig2 = px.bar(
        top_viral, x="Views/Hour", y="Title",
        orientation="h", title="🚀 Top 15 – Views/Hour (Velocity)",
        color="Views/Hour", color_continuous_scale="Purpor",
        template="plotly_dark",
        hover_data=["Views","Hours Ago"]
    )
    fig2.update_layout(paper_bgcolor="#0d0d1a", plot_bgcolor="#0d0d1a",
                       font_color="#c8c8ff", title_font_size=14,
                       yaxis=dict(autorange="reversed"),
                       coloraxis_showscale=False)
    st.plotly_chart(fig2, use_container_width=True)

# ──────────────────────────────────────────────
# CHARTS – Row 2: Engagement scatter + Duration dist
# ──────────────────────────────────────────────
st.markdown('<div class="section-title">🎯 Engagement & Content Analysis</div>', unsafe_allow_html=True)

c3, c4 = st.columns(2)

with c3:
    fig3 = px.scatter(
        df, x="Views", y="Engagement %",
        size="Comments", color="Category",
        hover_name="Title", template="plotly_dark",
        title="💡 Views vs Engagement % (bubble = comments)",
        color_discrete_sequence=px.colors.qualitative.Vivid
    )
    fig3.update_layout(paper_bgcolor="#0d0d1a", plot_bgcolor="#0d0d1a",
                       font_color="#c8c8ff", title_font_size=14)
    st.plotly_chart(fig3, use_container_width=True)

with c4:
    fig4 = px.histogram(
        df, x="Duration (min)", nbins=20,
        title="🕐 Video Duration Distribution",
        color_discrete_sequence=["#ff80bf"],
        template="plotly_dark"
    )
    fig4.update_layout(paper_bgcolor="#0d0d1a", plot_bgcolor="#0d0d1a",
                       font_color="#c8c8ff", title_font_size=14)
    st.plotly_chart(fig4, use_container_width=True)

# ──────────────────────────────────────────────
# CHARTS – Row 3: Category breakdown + Language
# ──────────────────────────────────────────────
st.markdown('<div class="section-title">🗂️ Category & Language Breakdown</div>', unsafe_allow_html=True)

c5, c6, c7 = st.columns(3)

with c5:
    cat_df = df["Category"].value_counts().reset_index()
    cat_df.columns = ["Category", "Count"]
    fig5 = px.pie(cat_df, values="Count", names="Category",
                  title="📂 Videos by Category",
                  color_discrete_sequence=px.colors.sequential.Plasma_r,
                  template="plotly_dark", hole=0.45)
    fig5.update_layout(paper_bgcolor="#0d0d1a", font_color="#c8c8ff", title_font_size=14)
    st.plotly_chart(fig5, use_container_width=True)

with c6:
    lang_df = df["Language"].value_counts().reset_index()
    lang_df.columns = ["Language", "Count"]
    fig6 = px.bar(lang_df.head(8), x="Language", y="Count",
                  title="🌐 Language Distribution",
                  color="Count", color_continuous_scale="Tealgrn",
                  template="plotly_dark")
    fig6.update_layout(paper_bgcolor="#0d0d1a", plot_bgcolor="#0d0d1a",
                       font_color="#c8c8ff", title_font_size=14,
                       coloraxis_showscale=False)
    st.plotly_chart(fig6, use_container_width=True)

with c7:
    loc_df = df["Location"].value_counts().reset_index()
    loc_df.columns = ["Location", "Count"]
    fig7 = px.bar(loc_df.head(8), x="Location", y="Count",
                  title="📍 Recording Location",
                  color="Count", color_continuous_scale="RdPu",
                  template="plotly_dark")
    fig7.update_layout(paper_bgcolor="#0d0d1a", plot_bgcolor="#0d0d1a",
                       font_color="#c8c8ff", title_font_size=14,
                       coloraxis_showscale=False)
    st.plotly_chart(fig7, use_container_width=True)

# ──────────────────────────────────────────────
# KEYWORD ANALYSIS
# ──────────────────────────────────────────────
st.markdown('<div class="section-title">🔑 Keyword & Tag Intelligence</div>', unsafe_allow_html=True)

all_tags = []
for t in df["Tags"].dropna():
    all_tags.extend([x.strip().lower() for x in t.split(",") if x.strip()])

# Title keywords
stopwords = {"the","a","an","is","in","of","to","and","for","on","at","by","with","this","that","|","-","#"}
title_words = []
for title in df["Title"].dropna():
    title_words.extend([w.lower() for w in re.findall(r'\b[a-zA-Z]{3,}\b', title) if w.lower() not in stopwords])

kw1, kw2 = st.columns(2)

with kw1:
    if all_tags:
        tag_counts = Counter(all_tags).most_common(20)
        tdf = pd.DataFrame(tag_counts, columns=["Tag","Count"])
        fig8 = px.treemap(tdf, path=["Tag"], values="Count",
                          title="🏷️ Top Tags Treemap",
                          color="Count", color_continuous_scale="Purpor",
                          template="plotly_dark")
        fig8.update_layout(paper_bgcolor="#0d0d1a", font_color="#c8c8ff", title_font_size=14)
        st.plotly_chart(fig8, use_container_width=True)
    else:
        st.info("No tag data available for this channel window.")

with kw2:
    if title_words:
        word_counts = Counter(title_words).most_common(15)
        wdf = pd.DataFrame(word_counts, columns=["Word","Count"])
        fig9 = px.bar(wdf, x="Count", y="Word", orientation="h",
                      title="📝 Top Title Keywords",
                      color="Count", color_continuous_scale="Magenta",
                      template="plotly_dark")
        fig9.update_layout(paper_bgcolor="#0d0d1a", plot_bgcolor="#0d0d1a",
                           font_color="#c8c8ff", title_font_size=14,
                           yaxis=dict(autorange="reversed"),
                           coloraxis_showscale=False)
        st.plotly_chart(fig9, use_container_width=True)

# ──────────────────────────────────────────────
# TOP VIDEOS TABLE
# ──────────────────────────────────────────────
st.markdown('<div class="section-title">📋 Full Video Data Table</div>', unsafe_allow_html=True)

display_cols = ["Title","Published (IST)","Hours Ago","Views","Likes",
                "Comments","Views/Hour","Engagement %","Duration (min)",
                "Category","Language","Location","Tag Count","Tags","URL"]

st.dataframe(
    df[display_cols].style.background_gradient(
        subset=["Views","Likes","Views/Hour","Engagement %"],
        cmap="RdPu"
    ).format({
        "Views": "{:,}", "Likes": "{:,}", "Comments": "{:,}",
        "Views/Hour": "{:,.1f}", "Engagement %": "{:.2f}%"
    }),
    use_container_width=True, height=400
)

# ──────────────────────────────────────────────
# TOP 5 SPOTLIGHT
# ──────────────────────────────────────────────
st.markdown('<div class="section-title">🏆 Top 5 Videos Spotlight</div>', unsafe_allow_html=True)

top5 = df.nlargest(5, "Views")
for _, row in top5.iterrows():
    with st.expander(f"▶ {row['Title'][:80]}"):
        cols = st.columns([3,1,1,1,1])
        cols[0].markdown(f"[🔗 Watch on YouTube]({row['URL']})")
        cols[1].metric("Views",    f"{row['Views']:,}")
        cols[2].metric("Likes",    f"{row['Likes']:,}")
        cols[3].metric("Comments", f"{row['Comments']:,}")
        cols[4].metric("Engmt%",   f"{row['Engagement %']}%")

        tag_html = "".join([f'<span class="tag-pill">{t.strip()}</span>'
                            for t in row["Tags"].split(",") if t.strip()])
        st.markdown(f"<div style='margin-top:8px'><b>🏷️ Tags:</b> {tag_html}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='info-box'><b>📝 Description:</b> {row['Description']}…</div>",
                    unsafe_allow_html=True)
        st.markdown(f"📂 **Category:** {row['Category']} &nbsp;|&nbsp; 🌐 **Language:** {row['Language']} "
                    f"&nbsp;|&nbsp; 📍 **Location:** {row['Location']} "
                    f"&nbsp;|&nbsp; 🕐 **Duration:** {row['Duration (min)']} min")

# ──────────────────────────────────────────────
# ADVANCED CORRELATION HEATMAP
# ──────────────────────────────────────────────
st.markdown('<div class="section-title">🔬 Metric Correlation Heatmap</div>', unsafe_allow_html=True)

num_cols = ["Views","Likes","Comments","Views/Hour","Engagement %","Duration (min)","Tag Count","Hours Ago"]
corr = df[num_cols].corr().round(2)

fig_h = go.Figure(data=go.Heatmap(
    z=corr.values, x=corr.columns.tolist(), y=corr.index.tolist(),
    colorscale="RdBu", zmid=0, text=corr.values,
    texttemplate="%{text}", textfont_size=11,
    hoverongaps=False
))
fig_h.update_layout(
    title="📊 How Metrics Correlate",
    paper_bgcolor="#0d0d1a", plot_bgcolor="#0d0d1a",
    font_color="#c8c8ff", height=420, title_font_size=14
)
st.plotly_chart(fig_h, use_container_width=True)

# ──────────────────────────────────────────────
# DATA SOURCE INFO
# ──────────────────────────────────────────────
st.divider()
st.markdown("""
<div class="info-box">
<b>📡 Data Sources & Notes</b><br><br>
• <b>Primary API:</b> YouTube Data API v3 — <code>search.list</code>, <code>videos.list</code> (statistics, snippet, contentDetails, topicDetails, recordingDetails)<br>
• <b>Auth:</b> API Key via environment variable <code>YOUTUBE_API_KEY</code><br>
• <b>Quota cost:</b> ~100 units / search page + 1 unit per video details batch<br>
• <b>Refresh rate:</b> Auto-cache clears every 5 minutes (Streamlit <code>@st.cache_data ttl=300</code>)<br>
• <b>Timezone:</b> All times displayed in Asia/Kolkata (IST, UTC+5:30)<br>
• <b>Engagement %:</b> <code>(Likes + Comments) / Views × 100</code><br>
• <b>Velocity:</b> <code>Views / max(hours_since_upload, 0.1)</code><br>
• <b>Location data:</b> Sourced from <code>recordingDetails.locationDescription</code> — only populated if creator sets it
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# REFRESH
# ──────────────────────────────────────────────
if st.button("🔄 Refresh Now"):
    st.cache_data.clear()
    st.rerun()
