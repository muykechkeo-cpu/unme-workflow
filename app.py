import os
import streamlit as st
from sqlalchemy import create_engine, text

# Page Configuration
st.set_page_config(
    page_title="UNME AI Social Media Management",
    page_icon="🚀",
    layout="wide"
)

# ----------------- DATABASE CONNECTION -----------------
DB_USER = "postgres"
DB_PASSWORD = "039601"  
DB_HOST = "127.0.0.1"
DB_PORT = "5432"
DB_NAME = "unme_social"

# តភ្ជាប់ដោយตรงជាមួយ Database តែម្តង ដើម្បីការពារការស្ទះ
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=disable"

@st.cache_resource
def get_db_engine():
    return create_engine(DATABASE_URL)

try:
    engine = get_db_engine()
    # ពិនិត្យការតភ្ជាប់
    with engine.connect() as conn:
        db_connected = True
except Exception as e:
    db_connected = False
    st.error(f"❌ មិនអាចតភ្ជាប់ទៅកាន់ Database បានទេ: {e}")

# ----------------- AUTHENTICATION SESSION -----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# ----------------- LOGIN / SIGN UP UI -----------------
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>Sign Up / Sign In</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>UNME AI Social Media Management</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        auth_mode = st.radio("ជ្រើសរើសជម្រើស", ["📝 Sign Up", "🔑 Sign In"], horizontal=True)
        
        email = st.text_input("Email address")
        password = st.text_input("Password", type="password")
        
        if auth_mode == "📝 Sign Up":
            if st.button("Sign Up", use_container_width=True):
                if email and password and db_connected:
                    try:
                        with engine.begin() as conn:
                            conn.execute(
                                text("INSERT INTO users (email, password) VALUES (:email, :password)"),
                                {"email": email, "password": password}
                            )
                        st.success("🎉 បង្កើតគណនីបានជោគជ័យ! សូមប្តូរទៅ Sign In វិញ។")
                    except Exception as e:
                        st.error(f"❌ មានបញ្ហាក្នុងការចុះឈ្មោះ (ពិនិត្យមើលថា Table users មានហើយឬยัง): {e}")
                else:
                    st.warning("⚠️ សូមបំពេញព័ត៌មាន ឬពិនិត្យការតភ្ជាប់ Database!")
                    
        else: # Sign In
            if st.button("Sign In", use_container_width=True):
                if email and password and db_connected:
                    try:
                        with engine.connect() as conn:
                            result = conn.execute(
                                text("SELECT * FROM users WHERE email = :email AND password = :password"),
                                {"email": email, "password": password}
                            ).fetchone()
                            
                        if result:
                            st.session_state.logged_in = True
                            st.session_state.user_email = email
                            st.rerun()
                        else:
                            st.error("❌ អ៊ីមែល ឬពាក្យសម្ងាត់មិនត្រឹមត្រូវឡើយ!")
                    except Exception as e:
                        st.error(f"❌ Database Error: {e}")
                else:
                    st.warning("⚠️ សូមបំពេញអ៊ីមែល និងពាក្យសម្ងាត់!")

else:
    st.sidebar.title(f"👤  ស្វាគមន៍: {st.session_state.user_email}")
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.rerun()
    
    st.title("🚀 UNME Main Dashboard")
    st.write("ยินดีต้อนรับเข้าสู่ระบบจัดการโซเชียลมีเดีย!")
