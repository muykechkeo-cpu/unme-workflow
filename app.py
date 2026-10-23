import os
import streamlit as st
from sqlalchemy import create_engine, text
from multi_platform import upload_to_facebook, upload_to_tiktok, upload_to_youtube

# Page Configuration
st.set_page_config(
    page_title="UNME AI Social Media Management",
    page_icon="🚀",
    layout="wide"
)

# ----------------- DATABASE CONFIGURATION & AUTO-CREATION -----------------
DB_USER = "postgres"
DB_PASSWORD = "039601"  
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "unme_social"

# ជំហានទី១៖ តភ្ជាប់ទៅកាន់ Server ដើម (postgres) ដើម្បីពិនិត្យ និងបង្កើត Database ថ្មីដោយស្វ័យប្រវត្តិ
default_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"
default_engine = create_engine(default_url, isolation_level="AUTOCOMMIT")

try:
    with default_engine.connect() as conn:
        result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")).fetchone()
        if not result:
            conn.execute(text(f"CREATE DATABASE {DB_NAME}"))
            st.toast(f"🎉 Created database: {DB_NAME}")
except Exception as e:
    st.error(f"❌ មិនអាចបង្កើត Database បានទេ: {e}")

# ជំហានទី២៖ តភ្ជាប់ចូលទៅកាន់ Database unme_social ផ្ទាល់ ដើម្បីបង្កើត Tables (users និង history)
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

@st.cache_resource
def get_db_engine():
    return create_engine(DATABASE_URL)

try:
    engine = get_db_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS history (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255),
                platform VARCHAR(50),
                content TEXT,
                status VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
except Exception as e:
    st.error(f"❌ មិនអាចបង្កើត Tables បានទេ: {e}")

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
                if email and password:
                    try:
                        with engine.begin() as conn:
                            conn.execute(
                                text("INSERT INTO users (email, password) VALUES (:email, :password)"),
                                {"email": email, "password": password}
                            )
                        st.success("🎉 បង្កើតគណនីបានជោគជ័យ! សូមប្តូរទៅ Sign In វិញ។")
                    except Exception as e:
                        st.error("❌ អ៊ីមែលនេះមានរួចរាល់ហើយ ឬមានបញ្ហាក្នុងការចុះឈ្មោះ!")
                else:
                    st.warning("⚠️ សូមបំពេញអ៊ីមែល និងពាក្យសម្ងាត់ឱ្យបានគ្រប់គ្រាន់!")
                    
        else: # Sign In
            if st.button("Sign In", use_container_width=True):
                if email and password:
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
    # ----------------- MAIN APP DASHBOARD -----------------
    st.sidebar.title(f"👤  ស្វាគមន៍: {st.session_state.user_email}")
    menu = st.sidebar.selectbox("មុខងារកម្មវិធី", ["📤 Upload & Publish", "📊 History Logs"])
    
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.rerun()

    if menu == "📤 Upload & Publish":
        st.title("🚀 UNME Multi-Platform Publisher")
        
        media_file = st.file_uploader("Upload Media (Video/Image)", type=["mp4", "jpg", "png", "jpeg"])
        caption = st.text_area("Caption / Title")
        platform = st.selectbox("Select Platform", ["Facebook", "TikTok", "YouTube"])
        
        if st.button("Publish Now"):
            if media_file:
                os.makedirs("uploaded", exist_ok=True)
                file_path = os.path.join("uploaded", media_file.name)
                with open(file_path, "wb") as f:
                    f.write(media_file.getbuffer())
                
                res = ""
                if platform == "Facebook":
                    res = upload_to_facebook(file_path, caption)
                elif platform == "TikTok":
                    res = upload_to_tiktok(file_path, caption)
                elif platform == "YouTube":
                    res = upload_to_youtube(file_path, caption, "Auto uploaded via UNME")
                
                st.success(f"លទ្ធផល៖ {res}")
                
                # រក្សាទុកប្រវត្តិ (History) ចូល PostgreSQL Database
                try:
                    with engine.begin() as conn:
                        conn.execute(
                            text("INSERT INTO history (email, platform, content, status) VALUES (:email, :platform, :content, :status)"),
                            {"email": st.session_state.user_email, "platform": platform, "content": caption, "status": "Success"}
                        )
                except Exception as e:
                    st.warning(f"⚠️ រក្សាទុក History មិនទាន់បាន៖ {e}")
            else:
                st.warning("⚠️ សូម Upload ឯកសារមេឌៀជាមុនសិន!")

    elif menu == "📊 History Logs":
        st.title("📊 Upload History Logs")
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT platform, content, status, created_at FROM history WHERE email = :email ORDER BY created_at DESC"),
                    {"email": st.session_state.user_email}
                ).fetchall()
                
            if result:
                for row in result:
                    st.info(f"**Platform:** {row[0]} | **Status:** {row[2]} | **Time:** {row[3]}\n\n**Content:** {row[1]}")
            else:
                st.write("មិនទាន់មានប្រវត្តិនៃការ Upload នៅឡើយទេ។")
        except Exception as e:
            st.error(f"❌ មិនអាចទាញយកទិន្នន័យ History បានទេ: {e}")
