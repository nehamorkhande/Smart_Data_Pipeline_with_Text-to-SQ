import streamlit as st
import sys,os
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from genai.langchain_chatbot import langchain_chat

if not st.session_state.get("logged_in"):
    st.switch_page("pages/0_Login.py")
    st.stop()

admin_id=st.session_state["admin_id"]
business_name=st.session_state["business_name"]
username=st.session_state["username"]

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono&display=swap');
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
    padding:9px 14px !important;transition:all 0.2s !important;
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
.page-sub { font-size:13px;color:#6b7280;margin:0 0 20px; }
[data-testid="stChatMessage"] {
    background:white !important;
    border:1px solid #f3f4f6 !important;
    border-radius:12px !important;
    padding:16px !important;
    margin-bottom:8px !important;
    box-shadow:0 1px 3px rgba(0,0,0,0.04) !important;
}
.lc-badge {
    display:inline-flex;align-items:center;gap:6px;
    background:#f0fdf4;border:1px solid #bbf7d0;
    border-radius:6px;padding:4px 10px;
    font-size:11px;color:#166534;font-weight:500;
    margin-bottom:20px;
}
.empty-wrap {
    text-align:center;padding:60px 20px;
}
.empty-icon  { font-size:52px;margin-bottom:16px; }
.empty-title {
    font-size:17px;font-weight:500;
    color:#374151;margin-bottom:8px;
}
.empty-sub {
    font-size:13px;color:#9ca3af;line-height:1.7;
}
.stButton > button {
    border-radius:8px !important;font-size:12px !important;
    font-weight:400 !important;transition:all 0.2s !important;
    border:1px solid #e5e7eb !important;
    background:white !important;color:#374151 !important;
}
.stButton > button:hover {
    border-color:#6366f1 !important;
    color:#6366f1 !important;
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
    <div style="font-size:10px;color:#374151;text-transform:uppercase;
                letter-spacing:0.8px;font-weight:500;padding:0 4px;
                margin-bottom:8px">Settings</div>
    """, unsafe_allow_html=True)
 
    use_sql = st.toggle("Use SQL Agent", value=True,
                        help="ON = queries DB automatically. OFF = general advice only")
 
    st.markdown("""
    <div style="height:1px;background:#1a1a1a;margin:14px 0"></div>
    """, unsafe_allow_html=True)
 
    if st.button("🗑️  Clear conversation",
                 use_container_width=True):
        st.session_state["chat_history"] = []
        st.rerun()
 
    if st.button("← Sign out", use_container_width=True):
        st.session_state.clear()
        st.switch_page("pages/0_Login.py")

st.markdown("""
<p class="page-title">🤖 AI Business Advisor</p>
<p class="page-sub">Powered by LangChain + Google Gemini —
asks your database and gives intelligent answers</p>
""", unsafe_allow_html=True)

st.markdown("""
<div class="lc-badge">
    🔗 LangChain SQL Agent + Gemini 1.5 Flash +
    ConversationBufferWindowMemory (last 5 messages)
</div>
""", unsafe_allow_html=True)

EXAMPLES = [
    "How is my business doing?",
    "What is my total revenue?",
    "Which product sells most?",
    "Who are top 5 customers?",
    "Show sales by category",
    "Which city has lowest sales?",
    "How many pending orders?",
    "Give me business suggestions",
    "What is my best selling day?",
    "Compare top vs bottom products",
    "Which payment mode is popular?",
    "Summarize this month"
]

st.markdown("""
<div style="font-size:11px;font-weight:500;color:#9ca3af;
            text-transform:uppercase;letter-spacing:0.8px;
            margin-bottom:10px">Try asking</div>
""", unsafe_allow_html=True)

cols=st.columns(4)
for i,ex in enumerate(EXAMPLES):
    with cols[i%4]:
        if st.button(ex, key=f"ex_{i}",
                     use_container_width=True):
            st.session_state["prefill"]=ex

if "chat_history" not in st.session_state:
    st.session_state["chat_history"]=[]

if not st.session_state["chat_history"]:
    st.markdown("""
    <div class="empty-wrap">
        <div class="empty-icon">🤖</div>
        <div class="empty-title">LangChain Business Advisor</div>
        <div class="empty-sub">
            I use LangChain SQL Agent to automatically query<br>
            your MySQL database and give intelligent answers.<br><br>
            Ask me about revenue, products, customers, trends<br>
            or anything about your business.
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    for chat in st.session_state["chat_history"]:
        with st.chat_message("user"):
            st.write(chat["question"])
        with st.chat_message("assistant"):
            st.markdown(chat["answer"])

prefill=st.session_state.pop("prefill","")
question=st.chat_input("Ask about your business...")
active=question or prefill

if active:
    with st.chat_message("user"):
        st.write(active)

    with st.chat_message("assistant"):
        with st.spinner(
            "LangChain agent querying your database..."
        ):
            answer=langchain_chat(
                question=active,
                admin_id=admin_id,
                business_name=business_name,
                chat_history=st.session_state["chat_history"],
                use_sql_agent=use_sql
            )
        st.markdown(answer)
    st.session_state["chat_history"].append({
        "question":active,
        "answer":answer
    })

