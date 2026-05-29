import streamlit as st
import pandas as pd
from db.connection import engine

if not st.session_state.get("logged_in"):
    st.switch_page("pages/0_Login.py")
    st.stop()

admin_id=st.session_state["admin_id"]
business_name=st.session_state["business_name"]
username=st.session_state["username"]

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&display=swap');
* { font-family: 'DM Sans', sans-serif; }
.stApp { background-color: #f8f9fb; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebarNav"] { display: none !important; }
[data-testid="stSidebar"] {
    background-color: #0f0f0f !important;
    border-right: 1px solid #1a1a1a;
}
[data-testid="stSidebar"] * { color: #9ca3af !important; }
[data-testid="stSidebarContent"] .stButton > button {
    background:#161616 !important;border:1px solid #222 !important;
    color:#6b7280 !important;border-radius:8px !important;
    font-size:13px !important;width:100% !important;
    padding:9px 14px !important;
}
[data-testid="stSidebarContent"] .stButton > button:hover {
    border-color:#6366f1 !important;color:#6366f1 !important;
}
[data-testid="stSidebar"] a {
    color:#6b7280 !important;font-size:13px !important;
    text-decoration:none !important;display:block !important;
    padding:8px 12px !important;border-radius:8px !important;
    transition:all 0.2s !important;margin-bottom:2px !important;
}
[data-testid="stSidebar"] a:hover {
    color:#6366f1 !important;background:#161616 !important;
}
.page-title {
    font-size:22px;font-weight:600;color:#111827;
    letter-spacing:-0.5px;margin:0 0 4px;
}
.page-sub { font-size:13px;color:#6b7280;margin:0 0 24px; }
.section-label {
    font-size:11px;font-weight:500;color:#9ca3af;
    text-transform:uppercase;letter-spacing:0.8px;margin:24px 0 12px;
}
[data-testid="metric-container"] {
    background:white !important;border:1px solid #f3f4f6 !important;
    border-radius:12px !important;padding:18px !important;
    box-shadow:0 1px 3px rgba(0,0,0,0.04) !important;
}
[data-testid="stMetricLabel"] {
    font-size:12px !important;color:#6b7280 !important;
}
[data-testid="stMetricValue"] {
    font-size:24px !important;font-weight:600 !important;
    color:#111827 !important;
}
[data-testid="stDataFrame"] {
    border-radius:10px !important;border:1px solid #f3f4f6 !important;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"""
    <div style="padding:20px 4px 16px">
        <div style="display:flex;align-items:center;gap:10px;
                    margin-bottom:14px">
            <div style="width:36px;height:36px;
                        background:linear-gradient(135deg,#6366f1,#10b981);
                        border-radius:9px;display:flex;
                        align-items:center;justify-content:center;
                        font-size:16px">📊</div>
            <div>
                <div style="font-size:13px;font-weight:500;
                            color:#e5e5e5">{business_name}</div>
                <div style="font-size:11px;color:#4b5563;
                            margin-top:1px">@{username}</div>
            </div>
        </div>
        <div style="height:1px;background:#1a1a1a;margin-bottom:14px"></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:10px;color:#374151;text-transform:uppercase;
                letter-spacing:0.8px;font-weight:500;padding:0 4px;
                margin-bottom:6px">Menu</div>
    """, unsafe_allow_html=True)
    st.page_link("pages/2_Upload_Data.py",   label="📂  Upload Data")
    st.page_link("pages/3_Dashboard.py",     label="📊  Dashboard")
    st.page_link("pages/4_Ask_AI.py",        label="🤖  Ask AI")
    st.page_link("pages/5_Upload_History.py",label="📋  Upload History")
    st.markdown("""
    <div style="height:1px;background:#1a1a1a;margin:14px 0"></div>
    """, unsafe_allow_html=True)
    if st.button("← Sign out", use_container_width=True):
        st.session_state.clear()
        st.switch_page("pages/0_Login.py")
 
st.markdown("""
<p class="page-title">📋 Upload History</p>
<p class="page-sub">All files uploaded by your store</p>
""", unsafe_allow_html=True)

try:
    logs=pd.read_sql("""
    SELECT
        file_name,
        total_rows,
        new_rows,
        duplicate_rows,
        missing_fixed,
        empty_removed,
        status,
        uploaded_at
        FROM upload_log
        WHERE admin_id=%s
        ORDER BY uploaded_at DESC
    """,engine,params=(admin_id,))
except Exception as e:
    st.error(f"Could not lead upload history: {e}")
    st.stop()

if logs.empty:
    st.info("No uploads yet. Go to Upload Data to started.")
    st.stop()

logs["uploaded_at"]=pd.to_datetime(logs["uploaded_at"])


st.markdown('<div class="section-label">Summary</div>',
            unsafe_allow_html=True)

summary=pd.read_sql("""
    SELECT
        COUNT(*) AS total_files,
        SUM(total_rows) AS total_rows,
        SUM(new_rows) AS total_new_rows,
        SUM(duplicate_rows) AS total_dupes,
        SUM(missing_fixed) AS total_missing_fixed,
        MAX(uploaded_at) AS last_upload
    FROM upload_log
    WHERE admin_id=%s                 
    """,engine,params=(admin_id,))

c1,c2,c3,c4 = st.columns(4)
c1.metric("Total files uploaded",
          int(summary["total_files"].iloc[0]))
c2.metric("Total rows loaded",
          f"{int(summary['total_new_rows'].iloc[0]):,}")
c3.metric("Total duplicates skipped",
          f"{int(summary['total_dupes'].iloc[0]):,}")
c4.metric("Last upload",
          str(summary["last_upload"].iloc[0])[:16]
          if summary["last_upload"].iloc[0] else "N/A")
 

st.markdown('<div class="section-label">Filter by date</div>',
            unsafe_allow_html=True)
 
today = pd.Timestamp.today()
c1,c2 = st.columns(2)
start = pd.Timestamp(c1.date_input(
    "From", today - pd.Timedelta(days=30)))
end   = pd.Timestamp(c2.date_input("To", today))
 
filtered = logs[
    (logs["uploaded_at"] >= start) &
    (logs["uploaded_at"] <= end)
]
 
st.caption(f"Showing {len(filtered)} of {len(logs)} uploads")
 
st.markdown('<div class="section-label">Upload records</div>',
            unsafe_allow_html=True)
st.dataframe(
    filtered.rename(columns={
        "file_name":      "File",
        "total_rows":     "Total Rows",
        "new_rows":       "New Rows",
        "duplicate_rows": "Duplicates",
        "missing_fixed":  "Missing Fixed",
        "empty_removed":  "Empty Removed",
        "status":         "Status",
        "uploaded_at":    "Uploaded At"
    }),
    use_container_width=True,
    hide_index=True
)
 