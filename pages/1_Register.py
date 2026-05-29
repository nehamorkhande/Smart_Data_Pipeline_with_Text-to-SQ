import streamlit as st
import hashlib
import pandas as pd
from db.connection import engine
from sqlalchemy import text

st.set_page_config(
    page_title="Create Account - Smart Data Pipeline",
    page_icon="📊",
    layout="centered"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&display=swap');
* { font-family: 'DM Sans', sans-serif; }
.stApp {
    background-color: #0f0f0f;
    background-image:
        radial-gradient(ellipse at 80% 20%, rgba(99,102,241,0.08) 0%, transparent 60%),
        radial-gradient(ellipse at 20% 80%, rgba(16,185,129,0.06) 0%, transparent 50%);
}
.main .block-container {
    max-width:      460px;
    padding-top:    60px;
    padding-bottom: 40px;
}
#MainMenu, footer, header { visibility: hidden; }

 
.brand-wrap { text-align:center; margin-bottom:28px; }
.brand-icon {
    width:52px;height:52px;
    background:linear-gradient(135deg,#6366f1,#10b981);
    border-radius:14px;display:inline-flex;
    align-items:center;justify-content:center;
    font-size:24px;margin-bottom:12px;
}
.brand-name {
    font-size:20px;font-weight:600;
    color:#f5f5f5;letter-spacing:-0.4px;margin:0;
}
 
.section-head {
    font-size:10px;color:#374151;
    text-transform:uppercase;letter-spacing:0.8px;
    font-weight:500;margin:20px 0 12px;
    padding-bottom:8px;border-bottom:1px solid #1a1a1a;
}
 
.stTextInput > div > div > input {
    background:    #0f0f0f !important;
    border:        1px solid #262626 !important;
    border-radius: 8px !important;
    color:         #e5e5e5 !important;
    font-size:     14px !important;
    padding:       10px 14px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #6366f1 !important;
    box-shadow:   0 0 0 3px rgba(99,102,241,0.12) !important;
}
.stTextInput label { color:#6b7280 !important; font-size:13px !important; }
.stTextInput > div > div > input::placeholder { color:#374151 !important; }
 
.stButton > button {
    width:100%;border-radius:8px !important;
    font-size:14px !important;font-weight:500 !important;
    padding:11px !important;transition:all 0.2s !important;
}
.stButton > button[kind="primary"] {
    background:linear-gradient(135deg,#6366f1,#5558e3) !important;
    color:white !important;border:none !important;
}
.stButton > button[kind="primary"]:hover {
    opacity:0.9 !important;transform:translateY(-1px) !important;
}
.back-wrap button {
    background:transparent !important;
    border:1px solid #262626 !important;
    color:#6b7280 !important;margin-top:8px !important;
}
.back-wrap button:hover {
    border-color:#6366f1 !important;
    color:#6366f1 !important;background:transparent !important;
    transform:none !important;
}
.terms {
    font-size:12px;color:#374151;
    text-align:center;margin-top:16px;line-height:1.7;
}
</style>
""", unsafe_allow_html=True)

if st.session_state.get("logged_in"):
    st.switch_page("pages/2_Upload_Data.py")

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def username_exists(u):
    try:
        r=pd.read_sql(
            "SELECT COUNT(*) as c FROM admins WHERE username=%s",
            engine, params=(u,))
        return r["c"][0]>0
    except: return False

def email_exists(e):
    try: 
        r=pd.read_sql(
            "SELECT COUNT(*) as c FROM admins WHERE email=%s",
            engine, params=(e,))
        return r["c"][0]>0
    except: return False

def register(username, password, business_name, email):
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO admins
                (username, password_hash, business_name, email)
                VALUES
                (:username, :password_hash, :business_name, :email)
            """),
            {
                "username": username,
                "password_hash": hash_password(password),
                "business_name": business_name,
                "email": email
            }
        )
        conn.commit()

st.markdown("""
<div class="brand-wrap">
    <div class="brand-icon">📊</div>
    <p class="brand-name">Create your account</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-head">Business information</div>',
            unsafe_allow_html=True)

business_name=st.text_input("Business name",
                            placeholder="e.g. Rahul Medical Store")

email=st.text_input("Email address",
                    placeholder="you@example.com")

st.markdown('<div class="section-head">Account credentials</div>',
            unsafe_allow_html=True)

username=st.text_input("Username",
                       placeholder="choose a username")

col1,col2=st.columns(2)

with col1:
    password=st.text_input("Password",type="password",
                           placeholder="min 6 characters")
    
with col2:
    confirm=st.text_input("Confirm password", type="password",
                          placeholder="repeat password")
    

if password:
    if len(password)<6:
        sc, sw, sl="#ef4444","30%","Weak"
    
    elif len(password)<10:
        sc,sw,sl="#f59e0b","65%","Medium"
    
    else:
        sc,sw,sl="#10b981","100%","Strong"

    st.markdown(f"""
    <div style="margin-top:-8px;margin-bottom:14px">
        <div style="background:#1a1a1a;border-radius:2px;height:3px">
            <div style="width:{sw};height:3px;background:{sc};
                        border-radius:2px;transition:all 0.3s"></div>
        </div>
        <span style="font-size:11px;color:{sc};margin-top:4px;
                     display:block">{sl} password</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
 
if st.button("Create account →",type="primary"):
    if not all([business_name, email,username, password, confirm]):
        st.error("Please fill in all fields")
    elif "@" not in email or "." not in email:
        st.error("Please enter a valid email address")
    elif len(username)<3:
        st.error("Username must be at least 3 characters")
    elif " " in username:
        st.error("Username cannot contain spaces")
    elif len(password)<6:
        st.error("Password must be at least 6 characters")
    elif password !=confirm:
        st.error("Passwords do not match")
    elif username_exists(username):
        st.error(f"Username '{username}' is already taken")
    elif email_exists(email):
        st.error("An account with this email already exists")
    else:
        try:
            register(username, password, business_name, email)
            st.success(
                f"Account created! Sign in with "
                f"username **{username}**"
            )
            st.balloons()
        except Exception as e:
            st.error(f"Something went wrong: {e}")

st.markdown("<div class='back-wrap'>", unsafe_allow_html=True)
if st.button("← Back to sign in"):
    st.switch_page("pages/0_Login.py")
st.markdown("</div>", unsafe_allow_html=True)
 
st.markdown("""
<div class="terms">
    Your data is stored securely and only visible to you.
</div>
""", unsafe_allow_html=True)

