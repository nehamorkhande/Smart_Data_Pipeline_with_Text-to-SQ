
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from genai.policy_rag import (save_policy, has_policy, get_policy_info,
                              delete_policy, search_policy, answer_from_policy)

if not st.session_state.get("logged_in"):
    st.switch_page("pages/0_Login.py")
    st.stop()

admin_id      = st.session_state["admin_id"]
business_name = st.session_state["business_name"]
username      = st.session_state["username"]

MAX_MB = 10

# ── Styles ────────────────────────────────────────────────────
st.markdown("""
<style>
.stApp { background-color: #f8f9fb; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebarNav"] { display: none !important; }
[data-testid="stSidebar"] { background-color: #0f0f0f !important; }
[data-testid="stSidebar"] * { color: #9ca3af !important; }
.page-title { font-size:22px; font-weight:600; color:#111827; margin:0 0 4px; }
.page-sub { font-size:13px; color:#6b7280; margin:0 0 20px; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"**{business_name}**  \n@{username}")
    st.markdown("---")
    st.page_link("pages/2_Upload_Data.py",    label="📂  Upload Data")
    st.page_link("pages/3_Dashboard.py",      label="📊  Dashboard")
    st.page_link("pages/4_Ask_AI.py",         label="🤖  Ask AI")
    st.page_link("pages/5_Upload_History.py", label="📋  Upload History")
    st.page_link("pages/6_Store_Policy.py",   label="📄  Store Policy")
    st.markdown("---")
    if st.button("← Sign out", use_container_width=True):
        st.session_state.clear()
        st.switch_page("pages/0_Login.py")

# ── Header ───────────────────────────────────────────────────
st.markdown('<p class="page-title">📄 Store Policy</p>', unsafe_allow_html=True)
st.markdown('<p class="page-sub">Upload your return / refund / warranty policy pdf. '
            'Then you can ask questions about it in Ask AI.</p>', unsafe_allow_html=True)

# ── Current policy ───────────────────────────────────────────
st.subheader("Current policy")
if has_policy(admin_id):
    info = get_policy_info(admin_id)
    st.success("File: " + info["file_name"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Pages", info["pages"])
    c2.metric("Chunks", info["chunks"])
    c3.metric("Uploaded", info["uploaded_at"])
    if st.button("🗑️ Delete this policy"):
        delete_policy(admin_id)
        st.rerun()
else:
    st.info("No policy uploaded yet.")

# ── Upload ───────────────────────────────────────────────────
st.subheader("Upload a policy pdf")
st.caption("A new upload replaces the old policy. Do not upload personal data of customers.")
uploaded = st.file_uploader("Choose a pdf file", type=["pdf"])

if uploaded is not None:
    size_mb = uploaded.size / (1024 * 1024)
    if size_mb > MAX_MB:
        st.error("File is too big (" + str(round(size_mb, 1)) + " MB). Maximum is " + str(MAX_MB) + " MB.")
    elif st.button("Process policy", type="primary"):
        with st.spinner("Reading the pdf and making embeddings (the first time it also downloads a small model)..."):
            ok, message = save_policy(admin_id, uploaded.name, uploaded)
        if ok:
            st.success(message)
            st.rerun()
        else:
            st.error(message)

# ── Try a question ───────────────────────────────────────────
if has_policy(admin_id):
    st.subheader("Try a question")
    question = st.text_input("Ask something about the policy", placeholder="How many days to return a product?")
    if st.button("Ask") and question.strip():
        with st.spinner("Searching the policy..."):
            answer = answer_from_policy(admin_id, business_name, question)
            hits = search_policy(admin_id, question)
        st.markdown(answer)
        with st.expander("Show the chunks that were found (for checking)"):
            for h in hits:
                st.write("Page " + str(h["page"]) + "  |  score " + str(round(h["score"], 2)))
                st.caption(h["text"])