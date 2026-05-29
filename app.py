# ============================================================
# app.py — Main entry point
# Smart Data Pipeline with Text-to-SQL
# ============================================================
import streamlit as st

st.set_page_config(
    page_title="Smart Data Pipeline",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Global CSS ───────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono&display=swap');

* { font-family: 'DM Sans', sans-serif; }

#MainMenu, footer, header { visibility: hidden; }
.stDeployButton            { display: none; }

/* ── Hide default nav ── */
[data-testid="stSidebarNav"] { display: none !important; }

/* ── Main background ── */
.stApp { background-color: #f8f9fb; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #0f0f0f !important;
    border-right:     1px solid #1a1a1a;
}
[data-testid="stSidebar"] * { color: #9ca3af !important; }

/* ── Sidebar buttons ── */
[data-testid="stSidebarContent"] .stButton > button {
    background:    #161616 !important;
    border:        1px solid #222 !important;
    color:         #6b7280 !important;
    border-radius: 8px !important;
    font-size:     13px !important;
    width:         100% !important;
    text-align:    left !important;
    padding:       9px 14px !important;
    transition:    all 0.2s !important;
    font-weight:   400 !important;
}
[data-testid="stSidebarContent"] .stButton > button:hover {
    border-color: #6366f1 !important;
    color:        #6366f1 !important;
}

/* ── Sidebar page links ── */
[data-testid="stSidebar"] a {
    color:           #6b7280 !important;
    font-size:       13px !important;
    text-decoration: none !important;
    display:         block !important;
    padding:         8px 12px !important;
    border-radius:   8px !important;
    transition:      all 0.2s !important;
    margin-bottom:   2px !important;
}
[data-testid="stSidebar"] a:hover {
    color:      #6366f1 !important;
    background: #161616 !important;
}

/* ── Primary buttons ── */
.stButton > button {
    border-radius: 8px !important;
    font-size:     13px !important;
    font-weight:   500 !important;
    font-family:   'DM Sans', sans-serif !important;
    transition:    all 0.2s !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg,#6366f1,#5558e3) !important;
    color:      white !important;
    border:     none !important;
}
.stButton > button[kind="primary"]:hover {
    opacity:   0.9 !important;
    transform: translateY(-1px) !important;
}

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background:    white !important;
    border:        1px solid #f3f4f6 !important;
    border-radius: 12px !important;
    padding:       18px !important;
    box-shadow:    0 1px 3px rgba(0,0,0,0.04) !important;
}
[data-testid="stMetricLabel"] {
    font-size:   12px !important;
    color:       #6b7280 !important;
    font-weight: 400 !important;
}
[data-testid="stMetricValue"] {
    font-size:   24px !important;
    font-weight: 600 !important;
    color:       #111827 !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background:    white !important;
    border:        2px dashed #e5e7eb !important;
    border-radius: 12px !important;
    padding:       12px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #6366f1 !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    border:        1px solid #f3f4f6 !important;
    overflow:      hidden !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input {
    border:        1px solid #e5e7eb !important;
    border-radius: 8px !important;
    font-size:     14px !important;
    padding:       10px 14px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #6366f1 !important;
    box-shadow:   0 0 0 3px rgba(99,102,241,0.12) !important;
}

/* ── Select box ── */
.stSelectbox > div > div {
    background:    white !important;
    border:        1px solid #e5e7eb !important;
    border-radius: 8px !important;
    font-size:     13px !important;
}

/* ── Alerts ── */
.stAlert {
    border-radius: 8px !important;
    font-size:     13px !important;
}

/* ── Progress bar ── */
.stProgress > div > div {
    background:    #6366f1 !important;
    border-radius: 4px !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    background:    white !important;
    border:        1px solid #e5e7eb !important;
    color:         #374151 !important;
    border-radius: 8px !important;
    font-size:     13px !important;
}
.stDownloadButton > button:hover {
    border-color: #6366f1 !important;
    color:        #6366f1 !important;
}

/* ── Chat ── */
[data-testid="stChatMessage"] {
    border-radius: 12px !important;
    border:        1px solid #f3f4f6 !important;
}

/* ── Divider ── */
hr {
    border-color: #f3f4f6 !important;
    margin:       20px 0 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar (only when logged in) ────────────────────────────
if st.session_state.get("logged_in"):
    business_name = st.session_state.get("business_name","")
    username      = st.session_state.get("username","")

    with st.sidebar:
        # ── Brand + user info ──────────────────────────────
        st.markdown(f"""
        <div style="padding:20px 4px 16px">
            <div style="display:flex;align-items:center;gap:10px;
                        margin-bottom:14px">
                <div style="width:36px;height:36px;
                            background:linear-gradient(135deg,#6366f1,#10b981);
                            border-radius:9px;display:flex;
                            align-items:center;justify-content:center;
                            font-size:16px;flex-shrink:0">📊</div>
                <div>
                    <div style="font-size:13px;font-weight:500;
                                color:#e5e5e5;line-height:1.3">
                        {business_name}</div>
                    <div style="font-size:11px;color:#4b5563;
                                margin-top:1px">@{username}</div>
                </div>
            </div>
            <div style="height:1px;background:#1a1a1a;
                        margin-bottom:14px"></div>
        </div>
        """, unsafe_allow_html=True)

        # ── Nav label ──────────────────────────────────────
        st.markdown("""
        <div style="font-size:10px;color:#374151;
                    text-transform:uppercase;letter-spacing:0.8px;
                    font-weight:500;padding:0 4px;
                    margin-bottom:6px">Menu</div>
        """, unsafe_allow_html=True)

        # ── Navigation links ───────────────────────────────
        st.page_link("pages/2_Upload_Data.py",
                     label="📂  Upload Data")
        st.page_link("pages/3_Dashboard.py",
                     label="📊  Dashboard")
        st.page_link("pages/4_Ask_AI.py",
                     label="🤖  Ask AI")
        st.page_link("pages/5_Upload_History.py",
                     label="📋  Upload History")

        # ── Divider ────────────────────────────────────────
        st.markdown("""
        <div style="height:1px;background:#1a1a1a;
                    margin:14px 0"></div>
        """, unsafe_allow_html=True)

        # ── Sign out ───────────────────────────────────────
        if st.button("← Sign out", use_container_width=True):
            st.session_state.clear()
            st.switch_page("pages/0_Login.py")

# ── Route ────────────────────────────────────────────────────
if not st.session_state.get("logged_in"):
    st.switch_page("pages/0_Login.py")
else:
    st.switch_page("pages/2_Upload_Data.py")