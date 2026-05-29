import streamlit as st
import pandas as pd
from io import BytesIO
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.cleaner import clean_dataframe
from pipeline.normalizer import normalize_and_load, log_upload

if not st.session_state.get("logged_in"):
    st.switch_page("pages/0_Login.py")
    st.stop()

admin_id      = st.session_state["admin_id"]
business_name = st.session_state["business_name"]
username      = st.session_state["username"]

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&display=swap');
* { font-family: 'DM Sans', sans-serif; }
.stApp { background-color: #f8f9fb; }
#MainMenu, footer { visibility: hidden; }
[data-testid="stSidebarNav"] { display: none !important; }

[data-testid="stSidebar"] {
    background-color: #0f0f0f !important;
    border-right: 1px solid #1a1a1a;
}
[data-testid="stSidebar"] * { color: #9ca3af !important; }
[data-testid="stSidebarContent"] .stButton > button {
    background: #161616 !important; border: 1px solid #222 !important;
    color: #6b7280 !important; border-radius: 8px !important;
    font-size: 13px !important; width: 100% !important;
    padding: 9px 14px !important; transition: all 0.2s !important;
    text-align: left !important;
}
[data-testid="stSidebarContent"] .stButton > button:hover {
    border-color: #6366f1 !important; color: #6366f1 !important;
}
.page-title {
    font-size: 22px; font-weight: 600; color: #111827;
    letter-spacing: -0.5px; margin: 0 0 4px;
}
.page-sub { font-size: 13px; color: #6b7280; margin: 0 0 24px; }
.section-label {
    font-size: 11px; font-weight: 500; color: #9ca3af;
    text-transform: uppercase; letter-spacing: 0.8px;
    margin: 24px 0 12px;
}
[data-testid="metric-container"] {
    background: white !important; border: 1px solid #f3f4f6 !important;
    border-radius: 12px !important; padding: 18px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}
[data-testid="stMetricLabel"] { font-size: 12px !important; color: #6b7280 !important; }
[data-testid="stMetricValue"] {
    font-size: 24px !important; font-weight: 600 !important; color: #111827 !important;
}
[data-testid="stFileUploader"] {
    background: white !important; border: 2px dashed #e5e7eb !important;
    border-radius: 12px !important; padding: 12px !important;
}
[data-testid="stFileUploader"]:hover { border-color: #6366f1 !important; }
[data-testid="stDataFrame"] {
    border-radius: 10px !important; border: 1px solid #f3f4f6 !important;
    overflow: hidden !important;
}
.stButton > button {
    border-radius: 8px !important; font-size: 13px !important;
    font-weight: 500 !important; transition: all 0.2s !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #5558e3) !important;
    color: white !important; border: none !important;
}
.stProgress > div > div { background: #6366f1 !important; border-radius: 4px !important; }
.stAlert { border-radius: 8px !important; font-size: 13px !important; }
.stDownloadButton > button {
    background: white !important; border: 1px solid #e5e7eb !important;
    color: #374151 !important; border-radius: 8px !important; font-size: 13px !important;
}
.file-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: #eff6ff; border: 1px solid #bfdbfe;
    border-radius: 6px; padding: 4px 10px; font-size: 12px;
    color: #1d4ed8; font-weight: 500; margin-bottom: 16px;
}
.divider { height: 1px; background: #f3f4f6; margin: 24px 0; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding:20px 4px 16px">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px">
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

    if st.button("📂  Upload Data",    use_container_width=True, key="nav_upload"):
        st.switch_page("pages/2_Upload_Data.py")
    if st.button("📊  Dashboard",      use_container_width=True, key="nav_dash"):
        st.switch_page("pages/3_Dashboard.py")
    if st.button("🤖  Ask AI",         use_container_width=True, key="nav_ai"):
        st.switch_page("pages/4_Ask_AI.py")
    if st.button("📋  Upload History", use_container_width=True, key="nav_hist"):
        st.switch_page("pages/5_Upload_History.py")

    st.markdown("""
    <div style="height:1px;background:#1a1a1a;margin:14px 0"></div>
    """, unsafe_allow_html=True)

    if st.button("← Sign out", use_container_width=True, key="nav_signout"):
        st.session_state.clear()
        st.switch_page("pages/0_Login.py")

# ── Main content ──────────────────────────────────────────────────────────────
st.markdown("""
<p class="page-title">Upload Sales Data</p>
<p class="page-sub">Upload your daily Excel file — 
system will clean and load it automatically</p>
""", unsafe_allow_html=True)

files = st.file_uploader(
    "Drop your Excel file here or click to browse",
    type=["xlsx", "xls"],
    accept_multiple_files=True
)

if not files:
    st.markdown("""
    <div style="text-align:center;padding:32px 0;
                color:#9ca3af;font-size:13px">
        Accepted formats: .xlsx and .xls · Multiple files allowed
    </div>
    """, unsafe_allow_html=True)
    st.stop()

for file in files:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="file-badge">📄 {file.name} · {file.size // 1024} KB</div>
    """, unsafe_allow_html=True)

    df = pd.read_excel(file)

    st.markdown('<div class="section-label">Basic info</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total rows",    f"{len(df):,}")
    c2.metric("Total columns", len(df.columns))
    c3.metric("File size",     f"{file.size // 1024} KB")

    total_cells    = df.shape[0] * df.shape[1]
    missing_cells  = int(df.isnull().sum().sum())
    duplicate_rows = int(df.duplicated().sum())
    missing_pct    = round(missing_cells / total_cells * 100, 2)  if total_cells > 0 else 0
    duplicate_pct  = round(duplicate_rows / len(df) * 100, 2)    if len(df) > 0    else 0
    bad_type_cols  = sum(
        1 for col in df.columns
        if df[col].dtype == object and
        pd.to_numeric(df[col], errors="coerce").notna().sum() > len(df) * 0.5
    )
    inconsistent_cols = sum(
        1 for col in df.select_dtypes(include="object").columns
        if df[col].dropna().astype(str).str.strip()
            .ne(df[col].dropna().astype(str)).any()
    )
    score = min(round(
        (missing_pct * 0.4) + (duplicate_pct * 0.3) +
        (bad_type_cols * 5) + (inconsistent_cols * 3)
    ), 100)

    st.markdown('<div class="section-label">Data quality report</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Missing cells",     missing_cells,  f"{missing_pct}%",   delta_color="inverse")
    c2.metric("Duplicate rows",    duplicate_rows, f"{duplicate_pct}%", delta_color="inverse")
    c3.metric("Wrong type cols",   bad_type_cols,  "numbers as text",   delta_color="inverse")
    c4.metric("Inconsistent cols", inconsistent_cols, "spaces / case",  delta_color="inverse")

    st.markdown('<div class="section-label">Messiness score</div>', unsafe_allow_html=True)
    label = "Mostly clean"    if score <= 20 else ("Needs cleaning" if score <= 50 else "Very messy")
    color = "normal"          if score <= 20 else ("off"            if score <= 50 else "inverse")
    st.metric("Score out of 100", f"{score} / 100", label, delta_color=color)
    st.progress(score)

    st.markdown('<div class="section-label">Column breakdown</div>', unsafe_allow_html=True)
    col_data = []
    for col in df.columns:
        n   = int(df[col].isnull().sum())
        pct = round(n / len(df) * 100, 1) if len(df) > 0 else 0
        col_data.append({
            "Column":   col,
            "Type":     str(df[col].dtype),
            "Missing":  n,
            "Missing%": f"{pct}%",
            "Status":   "✅ Clean"        if pct == 0 else
                        ("⚠️ Some missing" if pct < 30  else "❌ Mostly empty")
        })
    st.dataframe(pd.DataFrame(col_data), use_container_width=True, hide_index=True)
    st.dataframe(df.head(8),             use_container_width=True, hide_index=True)

    if st.button("🧹  Clean this file", key=f"clean_{file.name}"):
        with st.spinner("Cleaning your data..."):
            result = clean_dataframe(df, file.name)

        validation = result["validation"]

        if not result["success"]:
            st.error("Cannot process - required columns missing")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Missing required columns:**")
                for col in validation["missing_required"]:
                    st.markdown(f"- ❌ `{col}`")
            with c2:
                st.markdown("**Your file has:**")
                for col in df.columns:
                    st.markdown(f"- `{col}`")
            continue

        if validation["missing_optional"]:
            st.warning(
                f"Optional columns auto-filled: "
                f"{', '.join(validation['missing_optional'])}"
            )

        cleaned_df = result["dataframe"]
        st.success("Data cleaned successfully!")

        st.markdown('<div class="section-label">Cleaning summary</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Empty rows removed", result.get("empty_rows_removed", 0))
        c2.metric("Duplicates removed", result.get("duplicates_removed", 0))
        c3.metric("Missing fixed",      result.get("missing_fixed",      0))
        c4.metric("Final clean rows",   result.get("final_rows",         0))

        if result.get("outliers", 0) > 0:
            st.warning(f"⚠️ {result['outliers']} unusual transactions detected")
        if result.get("future_dates", 0) > 0:
            st.warning(f"⚠️ {result['future_dates']} future dates corrected")
        if result.get("missing_date_gaps"):
            gaps = result["missing_date_gaps"]
            st.warning(
                f"⚠️ No data for {len(gaps)} days: "
                f"{', '.join(gaps[:3])}{'...' if len(gaps) > 3 else ''}"
            )

        st.markdown('<div class="section-label">Before vs After</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.caption("BEFORE")
            st.dataframe(df.head(5),         use_container_width=True, hide_index=True)
        with col2:
            st.caption("AFTER")
            st.dataframe(cleaned_df.head(5), use_container_width=True, hide_index=True)

        st.session_state[f"cleaned_{file.name}"] = cleaned_df
        st.session_state[f"result_{file.name}"]  = result

    if f"cleaned_{file.name}" in st.session_state:
        col1, col2 = st.columns([2, 1])

        with col1:
            if st.button("💾  Load to database", key=f"load_{file.name}", type="primary"):
                cleaned_df = st.session_state[f"cleaned_{file.name}"]
                result     = st.session_state[f"result_{file.name}"]

                with st.spinner("Loading to database..."):
                    db_result = normalize_and_load(cleaned_df, admin_id)
                    try:
                        log_upload(
                            admin_id, file.name,
                            result.get("final_rows",         0),
                            db_result["new_rows"],
                            db_result["skipped"],
                            result.get("missing_fixed",      0),
                            result.get("empty_rows_removed", 0)
                        )
                    except: pass

                st.success("Data loaded to database!")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("New rows inserted",  db_result["new_rows"])
                c2.metric("Duplicates skipped", db_result["skipped"])
                c3.metric("Total customers",    db_result["customers"])
                c4.metric("Total products",     db_result["products"])

        with col2:
            buf = BytesIO()
            st.session_state[f"cleaned_{file.name}"] \
                .to_excel(buf, index=False, engine="openpyxl")
            buf.seek(0)
            st.download_button(
                "⬇️  Download cleaned",
                data=buf,
                file_name=f"cleaned_{file.name}",
                mime="application/vnd.ms-excel",
                key=f"dl_{file.name}"
            )