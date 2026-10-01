import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from google_auth import get_google_access_token
from google_sheets import SPREADSHEET_ID
from main import run_pipeline

st.set_page_config(page_title="AE Closer Call Log", page_icon="📞", layout="wide")

# ---------- Styling ----------
st.markdown("""
<style>
    .main > div { padding-top: 1.5rem; }
    h1 { font-weight: 700; letter-spacing: -0.5px; }
    .stMetric { background: #FAFAFA; border: 1px solid #ECECEC; border-radius: 10px; padding: 14px 18px; }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: 700; }
    .outcome-badge {
        display: inline-block; padding: 3px 10px; border-radius: 12px;
        font-size: 12px; font-weight: 600; white-space: nowrap;
    }
    .badge-closed { background: #E6F4EA; color: #1E7E34; }
    .badge-noclose { background: #FDECEA; color: #C0392B; }
    .badge-followup { background: #FFF4E5; color: #B7791F; }
    .badge-noshow { background: #EEF0F2; color: #5F6368; }
    .badge-review { background: #EDE7F6; color: #6A1B9A; }
    .block-container { max-width: 1400px; }
</style>
""", unsafe_allow_html=True)

COLUMNS = ["Closer Name", "Meeting ID", "Topic", "Start Time", "Duration (min)",
           "Recording Link", "Doc URL", "Logged At", "Prospect Name", "Outcome"]

BADGE_MAP = {
    "Closed/Deposit": "badge-closed",
    "No-close": "badge-noclose",
    "Follow-up": "badge-followup",
    "No-show": "badge-noshow",
    "Unclear - Review": "badge-review",
}


def fetch_all_rows():
    access_token = get_google_access_token()
    res = requests.get(
        f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/Sheet1!A2:J",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    res.raise_for_status()
    return res.json().get("values", [])


@st.cache_data(ttl=60)
def get_data():
    rows = fetch_all_rows()
    if not rows:
        return pd.DataFrame(columns=COLUMNS)
    df = pd.DataFrame(rows)
    df = df.reindex(columns=range(len(COLUMNS))).fillna("")
    df.columns = COLUMNS
    df["Duration (min)"] = pd.to_numeric(df["Duration (min)"], errors="coerce").fillna(0).astype(int)
    df["Start Time"] = pd.to_datetime(df["Start Time"], errors="coerce")
    return df


def outcome_badge(outcome):
    cls = BADGE_MAP.get(outcome, "badge-review")
    return f'<span class="outcome-badge {cls}">{outcome}</span>'


# ---------- Header ----------
col_title, col_logo = st.columns([5, 1])
with col_title:
    st.title("📞 AE Closer Call Log")
    st.caption("Zoom call transcripts, outcomes, and prospect data for all closers")

tab1, tab2 = st.tabs(["Call Log", "Run Pipeline"])

# ---------- Tab 1: Browse ----------
with tab1:
    df = get_data()

    if df.empty:
        st.info("No calls logged yet. Run the pipeline from the **Run Pipeline** tab to get started.")
    else:
        # Summary metrics
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Calls", len(df))
        m2.metric("Closed/Deposit", int((df["Outcome"] == "Closed/Deposit").sum()))
        m3.metric("Follow-up", int((df["Outcome"] == "Follow-up").sum()))
        m4.metric("No-show", int((df["Outcome"] == "No-show").sum()))
        m5.metric("Avg Duration", f'{int(df["Duration (min)"].mean())} min')

        st.markdown("---")

        # Filters
        f1, f2, f3, f4 = st.columns([2, 2, 2, 3])
        with f1:
            closer_filter = st.multiselect("Closer", sorted(df["Closer Name"].unique()))
        with f2:
            outcome_filter = st.multiselect("Outcome", sorted(df["Outcome"].unique()))
        with f3:
            min_duration = st.number_input("Min duration (min)", min_value=0, value=0, step=5)
        with f4:
            search = st.text_input("Search prospect name", placeholder="e.g. Ryan")

        filtered = df.copy()
        if closer_filter:
            filtered = filtered[filtered["Closer Name"].isin(closer_filter)]
        if outcome_filter:
            filtered = filtered[filtered["Outcome"].isin(outcome_filter)]
        if min_duration:
            filtered = filtered[filtered["Duration (min)"] >= min_duration]
        if search:
            filtered = filtered[filtered["Prospect Name"].str.contains(search, case=False, na=False)]

        filtered = filtered.sort_values("Start Time", ascending=False)

        st.caption(f"Showing {len(filtered)} of {len(df)} calls")

        display_df = filtered.copy()
        display_df["Outcome"] = display_df["Outcome"].apply(outcome_badge)
        display_df["Start Time"] = display_df["Start Time"].dt.strftime("%b %d, %Y %I:%M %p")
        display_df["Transcript"] = display_df["Doc URL"].apply(
            lambda u: f'<a href="{u}" target="_blank">Open ↗</a>' if u else ""
        )
        display_df["Recording"] = display_df["Recording Link"].apply(
            lambda u: f'<a href="{u}" target="_blank">Watch ↗</a>' if u else ""
        )

        show_cols = ["Closer Name", "Prospect Name", "Start Time", "Duration (min)", "Outcome", "Transcript", "Recording"]
        st.markdown(
            display_df[show_cols].to_html(escape=False, index=False, classes="styled-table"),
            unsafe_allow_html=True,
        )

        st.markdown("""
        <style>
            .main > div { padding-top: 1.5rem; }
            h1 { font-weight: 700; letter-spacing: -0.5px; }
            div[data-testid="stMetric"] {
                background: #1A1D24;
                border: 1px solid #2A2E37;
                border-radius: 10px;
                padding: 14px 18px;
            }
            div[data-testid="stMetricValue"] { font-size: 28px; font-weight: 700; }
            div[data-testid="stMetricLabel"] { color: #9AA0A6; }
            .outcome-badge {
                display: inline-block; padding: 3px 10px; border-radius: 12px;
                font-size: 12px; font-weight: 600; white-space: nowrap;
            }
            .badge-closed { background: #163A24; color: #4ADE80; }
            .badge-noclose { background: #3A1A17; color: #F87171; }
            .badge-followup { background: #3A2E12; color: #FBBF24; }
            .badge-noshow { background: #2A2E37; color: #9AA0A6; }
            .badge-review { background: #2E1F3D; color: #C084FC; }
            .styled-table { width: 100%; border-collapse: collapse; font-size: 14px; }
            .styled-table th { text-align: left; padding: 10px 12px; border-bottom: 2px solid #2A2E37; color: #9AA0A6; }
            .styled-table td { padding: 10px 12px; border-bottom: 1px solid #22252C; color: #E8EAED; }
            .styled-table tr:hover { background: #1A1D24; }
            .styled-table a { color: #60A5FA; text-decoration: none; }
            .block-container { max-width: 1400px; }
        </style>
        """, unsafe_allow_html=True)

    if st.button("🔄 Refresh data"):
        st.cache_data.clear()
        st.rerun()

# ---------- Tab 2: Run Pipeline ----------
with tab2:
    st.subheader("Pull new calls")
    st.caption("Fetches recordings for all closers, skips anything already logged.")

    days_back = st.slider("Look back (days)", 1, 14, 7)

    if st.button("▶️ Run Now", type="primary"):
        log_box = st.container(height=300)
        logs = []

        def log(msg):
            logs.append(msg)
            log_box.text("\n".join(logs))

        with st.spinner("Processing calls..."):
            total = run_pipeline(days_back=days_back, log=log)

        if total > 0:
            st.success(f"✅ Done — {total} new call(s) logged.")
        else:
            st.info("✅ Done — no new calls found.")
        st.cache_data.clear()