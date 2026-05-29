import streamlit as st
import hashlib 
import pandas as pd
from db.connection import engine

st.set_page_config(
    page_title="Smart Data Pipeline",
    page_icon="📊",
    layout="centered"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono&display=swap');
 
* { font-family: 'DM Sans', sans-serif; }
 
.stApp {
    background-color: #0f0f0f;
    background-image:
        radial-gradient(ellipse at 20% 50%, rgba(99,102,241,0.08) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 20%, rgba(16,185,129,0.06) 0%, transparent 50%);
}
 
.main .block-container {
    max-width: 420px;
    padding-top: 80px;
    padding-bottom: 40px;
}
 
/* Hide streamlit elements */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
 
/* Logo area */
.logo-wrap {
    text-align: center;
    margin-bottom: 40px;
}
.logo-icon {
    width: 48px;
    height: 48px;
    background: linear-gradient(135deg, #6366f1, #10b981);
    border-radius: 12px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    margin-bottom: 14px;
}
.logo-title {
    font-size: 22px;
    font-weight: 600;
    color: #f5f5f5;
    letter-spacing: -0.5px;
    margin: 0;
}
.logo-sub {
    font-size: 13px;
    color: #6b7280;
    margin: 4px 0 0;
}
 
/* Card */
.login-card {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 16px;
    padding: 32px;
    margin-bottom: 16px;
}
.card-title {
    font-size: 17px;
    font-weight: 500;
    color: #e5e5e5;
    margin: 0 0 6px;
}
.card-sub {
    font-size: 13px;
    color: #6b7280;
    margin: 0 0 24px;
}
 
/* Inputs */
.stTextInput > div > div > input {
    background: #111111 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    color: #e5e5e5 !important;
    font-size: 14px !important;
    padding: 10px 14px !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput > div > div > input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}
.stTextInput label {
    color: #9ca3af !important;
    font-size: 13px !important;
    font-weight: 400 !important;
}
 
/* Buttons */
.stButton > button {
    width: 100%;
    background: #6366f1 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 11px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    font-family: 'DM Sans', sans-serif !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
    letter-spacing: 0.1px !important;
}
.stButton > button:hover {
    background: #5558e3 !important;
    transform: translateY(-1px) !important;
}
 
/* Secondary button */
.secondary-btn > button {
    background: transparent !important;
    border: 1px solid #2a2a2a !important;
    color: #9ca3af !important;
}
.secondary-btn > button:hover {
    border-color: #6366f1 !important;
    color: #6366f1 !important;
    background: transparent !important;
    transform: none !important;
}
 
/* Alert messages */
.stAlert {
    border-radius: 8px !important;
    font-size: 13px !important;
}
 
/* Divider text */
.divider-text {
    text-align: center;
    color: #4b5563;
    font-size: 12px;
    margin: 16px 0;
    position: relative;
}
.divider-text::before, .divider-text::after {
    content: '';
    position: absolute;
    top: 50%;
    width: 42%;
    height: 1px;
    background: #2a2a2a;
}
.divider-text::before { left: 0; }
.divider-text::after  { right: 0; }
 
/* Demo accounts */
.demo-box {
    background: #111;
    border: 1px solid #222;
    border-radius: 10px;
    padding: 14px 16px;
    margin-top: 16px;
}
.demo-title {
    font-size: 11px;
    color: #4b5563;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 10px;
    font-weight: 500;
}
.demo-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
}
.demo-label {
    font-size: 12px;
    color: #6b7280;
    font-family: 'DM Mono', monospace;
}
.demo-value {
    font-size: 12px;
    color: #10b981;
    font-family: 'DM Mono', monospace;
}
</style>
""", unsafe_allow_html=True)

if st.session_state.get("logged_in"):
    st.switch_page("pages/2_upload.py")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(username,password):
    try:
        result=pd.read_sql(
            "SELECT admin_id, username, business_name, email "
            "FROM admins WHERE username=%s "
            "AND password_hash=%s AND is_active=TRUE",
            engine,
            params=(username, hash_password(password))
        )
        return result.iloc[0].to_dict() if len(result)==1 else None
    except Exception as e:
        return None
    
st.markdown("""
<div class="logo-wrap">
    <div class="logo-icon">📊</div>
    <p class="logo-title">Smart Data Pipeline</p>
    <p class="logo-sub">Text-to-SQL Analytics Platform</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="login-card">
    <p class="card-title">Welcome back</p>
    <p class="card-sub">Sign in to your store account</p>
</div>
""", unsafe_allow_html=True)

username=st.text_input("Username", placeholder="Enter your username")
password=st.text_input("Password", placeholder="Enter your password", type="password")

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

if st.button("Sign in", type="primary"):
    if not username or not password:
        st.error("Please enter your username and password")
    else:
        with st.spinner(""):
            admin=check_login(username, password)
        if admin:
            st.session_state["logged_in"]=True
            st.session_state["admin_id"]=int(admin["admin_id"])
            st.session_state["username"]=admin["username"]
            st.session_state["business_name"]=admin["business_name"]
            st.success(f"Welcome back, {admin['business_name']}!")
            st.switch_page("pages/2_Upload_Data.py")
        else:
            st.error("Incorrect username or password")

st.markdown("""
<div class="divider-text">or</div>
""", unsafe_allow_html=True)

with st.container():
    st.markdown("<div class='secondary-btn'>", unsafe_allow_html=True)
    if st.button("Create a new account"):
        st.switch_page("pages/1_Register.py")
    st.markdown("</div>", unsafe_allow_html=True)


st.markdown("""
<div class="demo-box">
    <div class="demo-title">Demo accounts</div>
    <div class="demo-row">
        <span class="demo-label">admin</span>
        <span class="demo-value">admin123</span>
    </div>
    <div class="demo-row">
        <span class="demo-label">store1</span>
        <span class="demo-value">store123</span>
    </div>
    <div class="demo-row" style="margin-bottom:0">
        <span class="demo-label">store2</span>
        <span class="demo-value">store456</span>
    </div>
</div>
""", unsafe_allow_html=True)
 



