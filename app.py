import os
import json
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
import openai
import gspread
from google.oauth2.service_account import Credentials
import datetime
import time
import threading
import cv2
from PIL import Image, ImageDraw, ImageFont
from multi_platform import upload_to_youtube, upload_to_tiktok, upload_to_facebook

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="UNME AI Social Media",
    page_icon="🚀",
    layout="wide"
)

# --- USER ACCOUNTS & ROLES DATABASE ---
# អ្នកអាចបន្ថែម User/Password និង Role (admin / member) នៅទីនេះ
USER_DB = {
    "admin": {
        "name": "Hab Rithy (Admin)",
        "password": "admin123", # គួរផ្លាស់ប្តូរ Password នេះ
        "role": "admin"
    },
    "staff": {
        "name": "Content Creator",
        "password": "staff123",
        "role": "member"
    }
}

# --- AUTHENTICATION SESSION MANAGEMENT ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["user_role"] = ""
    st.session_state["user_fullname"] = ""

def login_user(username, password):
    if username in USER_DB and USER_DB[username]["password"] == password:
        st.session_state["logged_in"] = True
        st.session_state["username"] = username
        st.session_state["user_role"] = USER_DB[username]["role"]
        st.session_state["user_fullname"] = USER_DB[username]["name"]
        return True
    return False

def logout_user():
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["user_role"] = ""
    st.session_state["user_fullname"] = ""

# --- MODERN ADVANCED CUSTOM CSS FOR UI STYLING ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 1.2rem !important;
            padding-bottom: 2.5rem !important;
            max-width: 95% !important;
        }
        .sticky-header {
            position: sticky;
            top: 0px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(8px);
            z-index: 99999;
            padding: 12px 20px;
            margin-bottom: 20px;
            border-bottom: 2px solid #eef2f6;
            border-radius: 0 0 12px 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        }
        .css-card {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #eef2f6;
            box-shadow: 0 2px 8px rgba(0,0,0,0.02);
            margin-bottom: 20px;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 48px;
            padding: 0px 24px;
            background-color: #f8fafc;
            border-radius: 10px;
            font-weight: 600;
            color: #475569;
            border: 1px solid #e2e8f0;
        }
        .stTabs [aria-selected="true"] {
            background-color: #2563eb !important;
            color: #ffffff !important;
            border-color: #2563eb !important;
            box-shadow: 0 4px 10px rgba(37, 99, 235, 0.2);
        }
        div.stButton > button {
            width: 100%;
            border-radius: 10px;
            font-weight: 600;
            padding: 10px 20px;
            transition: all 0.3s ease;
        }
        @media (prefers-color-scheme: dark) {
            .sticky-header {
                background: rgba(14, 17, 23, 0.95);
                border-bottom: 2px solid #262730;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }
            .css-card {
                background-color: #1e293b;
                border: 1px solid #334155;
            }
            .stTabs [data-baseweb="tab"] {
                background-color: #1e293b;
                color: #94a3b8;
                border: 1px solid #334155;
            }
            .stTabs [aria-selected="true"] {
                background-color: #2563eb !important;
                color: #ffffff !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# --- LOGIN SCREEN IF NOT LOGGED IN ---
if not st.session_state["logged_in"]:
    st.markdown("""
        <div style="text-align: center; padding-top: 50px;">
            <h1>🚀 UNME AI Social Media</h1>
            <p style="color: gray;">សូមចូលប្រើប្រាស់ប្រព័ន្ធ (System Login)</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        login_user_input = st.text_input("👤 ឈ្មោះអ្នកប្រើប្រាស់ (Username)")
        login_pass_input = st.text_input("🔑 ពាក្យសម្ងាត់ (Password)", type="password")
        
        if st.button("🔓 ចូលប្រព័ន្ធ (Login)", type="primary"):
            if login_user(login_user_input, login_pass_input):
                st.success("ចូលប្រព័ន្ធជោគជ័យ!")
                st.rerun()
            else:
                st.error("ឈ្មោះ ឬពាក្យសម្ងាត់មិនត្រឹមត្រូវទេ!")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()  # បញ្ឈប់ការ Run កូដខាងក្រោមប្រសិនបើមិនទាន់ Login

# --- MEDIA PROCESSING FUNCTIONS (WATERMARK & EDITING) ---
def process_image_watermark(input_path, output_path, watermark_text="UNME AI"):
    try:
        image = Image.open(input_path).convert("RGBA")
        draw = ImageDraw.Draw(image)
        width, height = image.size
        
        font_size = max(15, int(width / 25))
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
            
        text_bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        margin = 20
        x = width - text_width - margin
        y = height - text_height - margin
        
        draw.text((x+2, y+2), watermark_text, font=font, fill=(0, 0, 0, 180))
        draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 230))
        
        rgb_image = image.convert("RGB")
        rgb_image.save(output_path, "JPEG", quality=95)
        return output_path
    except Exception as e:
        print(f"Error processing image watermark: {e}")
        return input_path

def process_video_watermark(input_path, output_path, watermark_text="UNME AI"):
    try:
        cap = cv2.VideoCapture(input_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            org = (width - 250, height - 30)
            cv2.putText(frame, watermark_text, org, 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
            
            out.write(frame)

        cap.release()
        out.release()
        return output_path
    except Exception as e:
        print(f"Error processing video watermark: {e}")
        return input_path

# --- BACKGROUND SCHEDULER FUNCTION ---
def run_scheduled_jobs():
    while True:
        time.sleep(60)

if 'scheduler_started' not in st.session_state:
    st.session_state['scheduler_started'] = True
    bg_thread = threading.Thread(target=run_scheduled_jobs, daemon=True)
    bg_thread.start()

# --- SIDEBAR CONFIGURATION (ROLE RESTRICTED) ---
st.sidebar.title("⚙️ System Configuration")
st.sidebar.info(f"👤 **{st.session_state['user_fullname']}**\n\n🛡️ Role: **{st.session_state['user_role'].upper()}**")

if st.sidebar.button("🚪 ចាកចេញពីប្រព័ន្ធ (Logout)"):
    logout_user()
    st.rerun()

st.sidebar.markdown("---")

storage_mode = st.sidebar.selectbox(
    "📁 History Display Mode (ជ្រើសរើសប្រភេទបង្ហាញលើតារាង)",
    ["Local history.json", "Google Sheets"]
)

st.sidebar.markdown("---")

# 1. AI Provider Selection Expander
ai_provider = "Google Gemini"
gemini_api_key = os.getenv("GEMINI_API_KEY", "")
openai_api_key = os.getenv("OPENAI_API_KEY", "")
gsheet_json = os.getenv("GSHEET_JSON", "")
gsheet_url = os.getenv("GSHEET_URL", "")

# ប្រសិនបើជា Admin ទើបបង្ហាញ Expanders សម្រាប់កែ API Credentials
if st.session_state["user_role"] == "admin":
    with st.sidebar.expander("🤖 AI Provider Settings (Admin Only)", expanded=True):
        ai_provider = st.selectbox("ជ្រើសរើសប្រភេទ AI", ["Google Gemini", "OpenAI ChatGPT"])
        if ai_provider == "Google Gemini":
            gemini_api_key = st.text_input("Google Gemini API Key", value=gemini_api_key, type="password")
            if gemini_api_key:
                genai.configure(api_key=gemini_api_key)
        else:
            openai_api_key = st.text_input("OpenAI API Key", value=openai_api_key, type="password")
            if openai_api_key:
                openai.api_key = openai_api_key

    with st.sidebar.expander("📊 Google Sheets Configuration (Admin Only)", expanded=False):
        gsheet_json = st.text_area("Service Account JSON Key", value=gsheet_json)
        gsheet_url = st.text_input("Spreadsheet URL / ID", value=gsheet_url)

    with st.sidebar.expander("📘 Facebook Credentials (Admin Only)", expanded=False):
        fb_page_id = st.text_input("Facebook Page ID")
        fb_access_token = st.text_input("Facebook Access Token / API", type="password")

    with st.sidebar.expander("🎵 TikTok Credentials (Admin Only)", expanded=False):
        tiktok_token = st.text_input("TikTok Access Token", type="password", label_visibility="collapsed")

    with st.sidebar.expander("📺 YouTube Credentials (Admin Only)", expanded=False):
        yt_secret = st.text_input("YouTube Client Secret", type="password", label_visibility="collapsed")

    with st.sidebar.expander("🔔 Telegram Notification Settings (Admin Only)", expanded=False):
        tg_token = st.text_input("Telegram Bot Token", type="password")
        tg_chat_id = st.text_input("Telegram Chat ID")

    with st.sidebar.expander("⏰ Background Scheduler Settings (Admin Only)", expanded=False):
        schedule_freq = st.selectbox("Schedule Frequency", ["Manual", "Every 1 hour", "Every 6 hours", "Daily"], label_visibility="collapsed")
        st.caption("មុខងារ Auto Scheduler កំពុងដំណើរការក្នុងប្រព័ន្ធផ្ទៃខាងក្រោយ។")
else:
    st.sidebar.caption("🔒 ផ្នែកកែសម្រួល API Keys ត្រូវបានការពារ (សំរាប់តែ Admin)។")

# --- ABOUT & HOW TO USE SECTION IN SIDEBAR ---
st.sidebar.markdown("---")
with st.sidebar.expander("ℹ️ About & របៀបប្រើប្រាស់", expanded=False):
    st.markdown("""
    ### 🚀 អំពីកម្មវិធី (About)
    **UNME AI Social Media**  
    * **បង្កើតដោយ (by):** Hab Rithy  
    * **ជំនាន់ (Version):** 2.3 Pro (Multi-User RBAC Enabled)  
    """)

# --- MAIN INTERFACE (FIXED STICKY HEADER) ---
st.markdown(f"""
    <div class="sticky-header">
        <h1 style="margin:0; font-size: 26px; font-weight: 700; color: #1e293b;">🚀 UNME AI Social Media</h1>
        <p style="margin:2px 0 0 0; color: #64748b; font-size: 14px;">ប្រព័ន្ធគ្រប់គ្រង ស្វ័យប្រវត្តិកម្ម AI (by Hab Rithy) | គណនីបច្ចុប្បន្ន៖ <b>{st.session_state['user_fullname']}</b></p>
    </div>
""", unsafe_allow_html=True)

# --- REORDERED TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🚀 ផ្ទាំងគ្រប់គ្រងការផុស (Dashboard)", 
    "📈 Analytics Dashboard",
    "📊 ពិនិត្យប្រវត្តិការងារ (View History)", 
    "💬 Support Chat & AI Assistant"
])

# --- TAB 1: MAIN DASHBOARD ---
with tab1:
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.subheader("📌 ជ្រើសរើសប្រភេទនៃការផុស (Post Type)")
    post_type = st.radio(
        "តើអ្នកចង់ផុសមាតិកាប្រភេទណា?", 
        ["🎥 Video / Reels", "🖼️ Picture / Photo Posts"],
        horizontal=True
    )

    enable_watermark = st.checkbox("✨ បើកដំណើរការដាក់ Watermark ស្វ័យប្រវត្តិ", value=True)
    watermark_text = st.text_input("អត្ថបទ Watermark", value="UNME AI")

    media_file_path = None

    if post_type == "🎥 Video / Reels":
        uploaded_file = st.file_uploader("ជ្រើសរើសឯកសារវីដេអូផ្ទាល់ (.mp4, .mov, .avi)", type=["mp4", "mov", "avi"])
        if uploaded_file is not None:
            raw_path = os.path.join(".", "raw_" + uploaded_file.name)
            with open(raw_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            if enable_watermark:
                st.info("កំពុងច្នៃប្រឌិត និងដាក់ Watermark លើវីដេអូ...")
                media_file_path = os.path.join(".", "wm_" + uploaded_file.name)
                process_video_watermark(raw_path, media_file_path, watermark_text)
                st.success(f"បានដាក់ Watermark លើវីដេអូជោគជ័យ៖ {uploaded_file.name}")
            else:
                media_file_path = raw_path
                st.success(f"បានផ្ទុកឡើងវីដេអូ៖ {uploaded_file.name}")
    else:
        uploaded_image = st.file_uploader("ជ្រើសរើសរូបភាពសម្រាប់ផុស (.jpg, .jpeg, .png)", type=["jpg", "jpeg", "png"])
        if uploaded_image is not None:
            raw_path = os.path.join(".", "raw_" + uploaded_image.name)
            with open(raw_path, "wb") as f:
                f.write(uploaded_image.getbuffer())
                
            if enable_watermark:
                st.info("កំពុងច្នៃប្រឌិត និងដាក់ Watermark លើរូបភាព...")
                media_file_path = os.path.join(".", "wm_" + uploaded_image.name)
                process_image_watermark(raw_path, media_file_path, watermark_text)
                st.success(f"បានដាក់ Watermark លើរូបភាពជោគជ័យ៖ {uploaded_image.name}")
            else:
                media_file_path = raw_path
                st.success(f"បានផ្ទុកឡើងរូបភាព៖ {uploaded_image.name}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.subheader(f"🤖 ការកំណត់ស្ទីល និងជំនួយការពី {ai_provider}")
    caption_prompt = st.text_area(
        "សរសេរពាក្យបញ្ជា ឬស្ទីលដែលចង់បានឱ្យ AI បង្កើត៖",
        placeholder="ឧទាហរណ៍៖ សរសេរ Caption ជាភាសាខ្មែរឱ្យទាក់ទាញបែបកំប្លែង ព្រមទាំង Hashtags ល្បីៗ..."
    )

    generated_caption = ""
    if st.button(f"✨ បង្កើត Caption ដោយប្រើ {ai_provider}", type="primary"):
        if ai_provider == "Google Gemini":
            if gemini_api_key:
                try:
                    genai.configure(api_key=gemini_api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(f"Write a social media caption and hashtags based on this prompt: {caption_prompt}")
                    generated_caption = response.text
                    st
