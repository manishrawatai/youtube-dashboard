import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pytz

# -----------------------
# CONFIG
# -----------------------
API_KEY = "AIzaSyBSrbelc7tKIW_LPfCdL1A3bMLsVe0HAjs"
CHANNEL_ID = "UCwqusr8YDwM-3mEYTDeJHzw"

youtube = build("youtube", "v3", developerKey=API_KEY)

st.set_page_config(page_title="YouTube Live Dashboard", layout="wide")

st.title("📺 YouTube Live Dashboard (Last 12 Hours)")
st.markdown("Tracking latest uploads and performance")

# -----------------------
# FETCH DATA FUNCTION
# -----------------------
@st.cache_data(ttl=300)  # refresh every 5 mins
def fetch_data():
    now = datetime.utcnow()
    last_12_hours = now - timedelta(hours=12)
    published_after = last_12_hours.isoformat("T") + "Z"

    video_ids = []
    video_data = []

    next_page_token = None

    while True:
        request = youtube.search().list(
            part="snippet",
            channelId=CHANNEL_ID,
            maxResults=50,
            order="date",
            publishedAfter=published_after,
            type="video",
            pageToken=next_page_token
        )

        response = request.execute()

        for item in response.get("items", []):
            video_id = item["id"]["videoId"]
            snippet = item["snippet"]

            video_ids.append(video_id)

            video_data.append({
                "title": snippet["title"],
                "published_at": snippet["publishedAt"],
                "video_id": video_id
            })

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    stats_map = {}

    if video_ids:
        for i in range(0, len(video_ids), 50):
            stats_request = youtube.videos().list(
                part="statistics",
                id=",".join(video_ids[i:i+50])
            )
            stats_response = stats_request.execute()

            for item in stats_response.get("items", []):
                stats_map[item["id"]] = int(item["statistics"].get("viewCount", 0))

    ist = pytz.timezone("Asia/Kolkata")
    final_data = []

    for video in video_data:
        utc_time = datetime.strptime(video["published_at"], "%Y-%m-%dT%H:%M:%SZ")
        utc_time = utc_time.replace(tzinfo=pytz.utc)
        ist_time = utc_time.astimezone(ist)

        hours_since = (datetime.now(pytz.utc) - utc_time).total_seconds() / 3600

        final_data.append({
            "Title": video["title"],
            "Published": ist_time,
            "Hours Ago": round(hours_since, 2),
            "Views": stats_map.get(video["video_id"], 0),
            "Views/Hour": round(stats_map.get(video["video_id"], 0) / max(hours_since, 0.1), 2),
            "URL": f"https://youtube.com/watch?v={video['video_id']}"
        })

    df = pd.DataFrame(final_data)

    if not df.empty:
        df = df.sort_values(by="Published", ascending=False)

    return df


# -----------------------
# LOAD DATA
# -----------------------
df = fetch_data()

if df.empty:
    st.warning("No videos found in last 12 hours")
else:
    # KPIs
    col1, col2, col3 = st.columns(3)

    col1.metric("📹 Total Videos", len(df))
    col2.metric("👀 Total Views", int(df["Views"].sum()))
    col3.metric("🔥 Avg Views/Hour", round(df["Views/Hour"].mean(), 2))

    st.divider()

    # -----------------------
    # TABLE
    # -----------------------
    st.subheader("📊 Latest Videos")
    st.dataframe(df)

    # -----------------------
    # TOP 10
    # -----------------------
    st.subheader("🔥 Top 10 Videos (Views)")
    top10 = df.sort_values(by="Views", ascending=False).head(10)

    st.bar_chart(top10.set_index("Title")["Views"])

    # -----------------------
    # VIRAL VIDEOS
    # -----------------------
    st.subheader("🚀 Viral Videos (Views/Hour)")
    viral = df.sort_values(by="Views/Hour", ascending=False).head(10)

    st.bar_chart(viral.set_index("Title")["Views/Hour"])

    # -----------------------
    # TIMELINE
    # -----------------------
    st.subheader("📈 Upload Timeline")
    timeline = df.sort_values("Published")

    st.line_chart(timeline.set_index("Published")["Views"])

    # -----------------------
    # AUTO REFRESH BUTTON
    # -----------------------
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

        st.experimental_rerun()