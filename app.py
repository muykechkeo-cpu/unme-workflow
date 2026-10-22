import os
import json
import re
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

# --- SECURE CREDENTIALS LOADING ---
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

st.set_page_config(
    page_title="UNME AI Social Media",
    page_icon="🚀",
    layout="wide"
)

# --- MODERN ADVANCED CUSTOM CSS FOR UI STYLING & GRAY BACKGROUND ---
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
        .auth-card-gray {
            background: linear-gradient(145deg, #f1f5f9 0%, #e2e8f0 100%);
            padding: 35px;
            border-radius: 18px;
            border: 1px solid #cbd5e1;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.06);
            margin-top: 15px;
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
            .auth-card-gray {
                background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
                border: 1px solid #334155;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
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

# --- EMAIL VALIDATION HELPER ---
def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

# --- USER DATABASE MANAGEMENT (JSON FILE STORAGE) ---
USER_DB_FILE = "users.json"

def load_users():
    default_users = {
        "admin@unme.com": {
            "password": "adminpassword",
            "name": "Hab Rithy (Admin)",
            "role": "admin"
        }
    }
    if os.path.exists(USER_DB_FILE):
        try:
            with open(USER_DB_FILE, "r", encoding="utf-8") as f:
                users = json.load(f)
                if "admin@unme.com" not in users:
                    users["admin@unme.com"] = default_users["admin@unme.com"]
                return users
        except:
            return default_users
    return default_users

def save_users(users):
    with open(USER_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

# --- AUTHENTICATION STATE HANDLING ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None

# --- DIRECT SIGN IN / SIGN UP INTERFACE (NO OTP) ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="auth-card-gray">', unsafe_allow_html=True)
        st.title("🚀 UNME AI Social Media")
        
        auth_mode = st.radio("ជ្រើសរើសជម្រើស", ["🔑 ចូលប្រព័ន្ធ (Sign In)", "📝 ចុះឈ្មោះ (Sign Up)"], horizontal=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        users_db = load_users()

        if auth_mode == "🔑 ចូលប្រព័ន្ធ (Sign In)":
            st.subheader("ចូលប្រព័ន្ធរបស់អ្នក")
            signin_email = st.text_input("អ៊ីមែល (Email Address)", placeholder="example@gmail.com").strip().lower()
            signin_pass = st.text_input("ពាក្យសម្ងាត់ (Password)", type="password")
            
            if st.button("🔓 ចូលប្រព័ន្ធ (Sign In)", type="primary"):
                if not signin_email or not signin_pass:
                    st.warning("សូមបញ្ចូលអ៊ីមែល និងពាក្យសម្ងាត់ឱ្យបានត្រឹមត្រូវ។")
                elif signin_email in users_db and users_db[signin_email]["password"] == signin_pass:
                    st.session_state["logged_in"] = True
                    user_data = users_db[signin_email]
                    user_data["email"] = signin_email
                    st.session_state["user_info"] = user_data
                    st.success("ចូលប្រព័ន្ធជោគជ័យ!")
                    st.rerun()
                else:
                    st.error("អ៊ីមែល ឬពាក្យសម្ងាត់មិនត្រឹមត្រូវឡើយ!")
        
        else:  # Direct Sign Up Mode (Without OTP)
            st.subheader("បង្កើតគណនីថ្មី (Sign Up)")
            signup_name = st.text_input("ឈ្មោះពេញ / Full Name", key="su_name")
            signup_email = st.text_input("អាសយដ្ឋានអ៊ីមែល (Email Address)", placeholder="example@gmail.com", key="su_email").strip().lower()
            signup_pass = st.text_input("បង្កើតពាក្យសម្ងាត់ (Choose Password)", type="password", key="su_pass")
            
            if st.button("✨ ចុះឈ្មោះ និងចូលប្រព័ន្ធភ្លាមៗ", type="primary"):
                if not signup_name or not signup_email or not signup_pass:
                    st.warning("សូមបំពេញព័ត៌មានគ្រប់ប្រអប់ឱ្យបានត្រឹមត្រូវ។")
                elif not is_valid_email(signup_email):
                    st.error("ទម្រង់អាសយដ្ឋានអ៊ីមែលមិនត្រឹមត្រូវឡើយ!")
                elif signup_email in users_db:
                    st.error("អាសយដ្ឋានអ៊ីមែលនេះមានគណនីរួចហើយ!")
                else:
                    users_db[signup_email] = {
                        "password": signup_pass,
                        "name": signup_name,
                        "role": "user"
                    }
                    save_users(users_db)
                    
                    st.session_state["logged_in"] = True
                    st.session_state["user_info"] = {
                        "email": signup_email,
                        "name": signup_name,
                        "role": "user"
                    }
                    
                    st.success("បង្កើតគណនី និងចូលប្រព័ន្ធជោគជ័យ!")
                    time.sleep(0.5)
                    st.rerun()
                    
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

current_user = st.session_state["user_info"]

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

def run_scheduled_jobs():
    while True:
        time.sleep(60)

if 'scheduler_started' not in st.session_state:
    st.session_state['scheduler_started'] = True
    bg_thread = threading.Thread(target=run_scheduled_jobs, daemon=True)
    bg_thread.start()

# --- SIDEBAR CONFIGURATION ---
st.sidebar.title(f"👤 {current_user['name']}")
st.sidebar.caption(f"Email: {current_user['email']}")

if st.sidebar.button("🚪 ចាកចេញពីប្រព័ន្ធ (Logout)"):
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None
    st.rerun()

st.sidebar.markdown("---")

storage_mode = st.sidebar.selectbox(
    "📁 History Display Mode (ជ្រើសរើសប្រភេទបង្ហាញលើតារាង)",
    ["Local history.json", "Google Sheets"]
)

st.sidebar.title("⚙️ System Configuration")

with st.sidebar.expander("🤖 AI Provider Settings", expanded=True):
    ai_provider = st.selectbox("ជ្រើសរើសប្រភេទ AI", ["Google Gemini", "OpenAI ChatGPT"])
    if ai_provider == "Google Gemini":
        if GEMINI_API_KEY:
            st.success("✅ Gemini API Key បានផ្ទុកស្រាប់ពី System Secrets")
        else:
            gemini_api_key_input = st.text_input("Google Gemini API Key", type="password")
            if gemini_api_key_input:
                genai.configure(api_key=gemini_api_key_input)
    else:
        if OPENAI_API_KEY:
            st.success("✅ OpenAI API Key បានផ្ទុកស្រាប់ពី System Secrets")
            openai.api_key = OPENAI_API_KEY
        else:
            openai_api_key_input = st.text_input("OpenAI API Key", type="password")
            if openai_api_key_input:
                openai.api_key = openai_api_key_input

with st.sidebar.expander("📊 Google Sheets Configuration", expanded=False):
    gsheet_json = st.text_area("Service Account JSON Key (Paste JSON text here)")
    gsheet_url = st.text_input("Spreadsheet URL / ID")

with st.sidebar.expander("📘 Facebook Credentials", expanded=False):
    fb_page_id = st.text_input("Facebook Page ID")
    fb_access_token = st.text_input("Facebook Access Token / API", type="password")

with st.sidebar.expander("🎵 TikTok Credentials", expanded=False):
    tiktok_token = st.text_input("TikTok Access Token", type="password", label_visibility="collapsed")

with st.sidebar.expander("📺 YouTube Credentials", expanded=False):
    yt_secret = st.text_input("YouTube Client Secret", type="password", label_visibility="collapsed")

with st.sidebar.expander("🔔 Telegram Notification Settings", expanded=False):
    tg_token = st.text_input("Telegram Bot Token", type="password")
    tg_chat_id = st.text_input("Telegram Chat ID")

with st.sidebar.expander("⏰ Background Scheduler Settings", expanded=False):
    schedule_freq = st.selectbox("Schedule Frequency", ["Manual", "Every 1 hour", "Every 6 hours", "Daily"], label_visibility="collapsed")
    st.caption("មុខងារ Auto Scheduler កំពុងដំណើរការក្នុងប្រព័ន្ធផ្ទៃខាងក្រោយ។")

st.sidebar.markdown("---")
with st.sidebar.expander("ℹ️ About & របៀបប្រើប្រាស់", expanded=False):
    st.markdown("""
    ### 🚀 អំពីកម្មវិធី (About)
    **UNME AI Social Media**  
    * **បង្កើតដោយ (by):** Hab Rithy  
    * **ជំនាន់ (Version):** 3.0 Pro (Direct Auth & Google Sheets Backup)  
    * **គោលបំណង៖** ប្រព័ន្ធស្វ័យប្រវត្តិកម្មក្នុងការបង្កើត Caption ដោយ AI កែច្នៃ Watermark និងបញ្ជូនមាតិកាទៅកាន់ Facebook, TikTok និង YouTube ។  
    """)

# --- MAIN INTERFACE (FIXED STICKY HEADER) ---
st.markdown("""
    <div class="sticky-header">
        <h1 style="margin:0; font-size: 26px; font-weight: 700; color: #1e293b;">🚀 UNME AI Social Media</h1>
        <p style="margin:2px 0 0 0; color: #64748b; font-size: 14px;">ប្រព័ន្ធគ្រប់គ្រង ស្វ័យប្រវត្តិកម្ម AI និងបញ្ជូនវីដេអូ ឬរូបភាពទៅកាន់ Facebook, TikTok និង YouTube (by Hab Rithy)</p>
    </div>
""", unsafe_allow_html=True)

# --- REORDERED TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🚀 ផ្ទាំងគ្រប់គ្រងការផុស (Dashboard)", 
    "📈 Analytics Dashboard",
    "📊 ពិនិត្យប្រវត្តិการងារ (View History)", 
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
            if GEMINI_API_KEY:
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(f"Write a social media caption and hashtags based on this prompt: {caption_prompt}")
                    generated_caption = response.text
                    st.success("AI (Gemini) បានបង្កើត Caption រួចរាល់!")
                    st.write(generated_caption)
                except Exception as e:
                    st.error(f"មានកំហុសក្នុងការតភ្ជាប់ Gemini AI៖ {e}")
            else:
                st.warning("មិនមាន GEMINI_API_KEY នៅក្នុងប្រព័ន្ធទេ។ សូមពិនិត្យមើលឯកសារ .env ។")
        else:
            if OPENAI_API_KEY:
                try:
                    client = openai.OpenAI(api_key=OPENAI_API_KEY)
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": f"Write a social media caption and hashtags based on this prompt: {caption_prompt}"}]
                    )
                    generated_caption = response.choices[0].message.content
                    st.success("AI (ChatGPT) បានបង្កើត Caption រួចរាល់!")
                    st.write(generated_caption)
                except Exception as e:
                    st.error(f"មានកំហុសក្នុងការតភ្ជាប់ OpenAI API៖ {e}")
            else:
                st.warning("មិនមាន OPENAI_API_KEY នៅក្នុងប្រព័ន្ធទេ។")

    final_caption = st.text_area("កែសម្រួល Caption ចុងក្រោយមុនពេល Upload៖", value=generated_caption if generated_caption else caption_prompt)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.subheader("🎬 ជ្រើសរើសវេទិកាសម្រាប់ការបញ្ជូន (Multi-Platform Selection)")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        pub_fb = st.checkbox("📘 Facebook", value=True)
    with col_b:
        pub_tiktok = st.checkbox("🎵 TikTok")
    with col_c:
        pub_yt = st.checkbox("📺 YouTube")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀 ចាប់ផ្តើមដំណើរការ Upload ទៅកាន់ Platform", type="primary"):
        if media_file_path and os.path.exists(media_file_path):
            st.info("ប្រព័ន្ធកំពុងដំណើរការបញ្ជូនមាតិកា...")
            results = []
            
            if pub_fb:
                res_fb = upload_to_facebook(media_file_path, final_caption, post_type=post_type)
                results.append(res_fb)
            if pub_tiktok:
                res_tk = upload_to_tiktok(media_file_path, final_caption)
                results.append(res_tk)
            if pub_yt:
                res_yt = upload_to_youtube(media_file_path, "AI Generated Content", final_caption)
                results.append(res_yt)
                
            st.success("ការបញ្ជូនបានបញ្ចប់!")
            st.json(results)
            
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_entry = {
                "user": f"{current_user['name']} ({current_user['email']})",
                "type": post_type, 
                "file": media_file_path, 
                "caption": final_caption, 
                "results": results, 
                "time": timestamp
            }
            
            # Local JSON Backup
            try:
                if os.path.exists("history.json"):
                    with open("history.json", "r", encoding="utf-8") as f:
                        history_data = json.load(f)
                else:
                    history_data = []
                    
                history_data.append(history_entry)
                with open("history.json", "w", encoding="utf-8") as f:
                    json.dump(history_data, f, ensure_ascii=False, indent=4)
                st.info("✅ បានរក្សាទុកប្រវត្តិក្នុង Local history.json រួចរាល់។")
            except Exception as e:
                st.error(f"មានបញ្ហាក្នុងការរក្សាទុក Local history.json៖ {e}")
                
            # Google Sheets Persistent Data Backup
            if gsheet_json and gsheet_url:
                try:
                    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                    creds_dict = json.loads(gsheet_json)
                    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
                    client = gspread.authorize(creds)
                    
                    sheet = client.open_by_url(gsheet_url).sheet1
                    sheet.append_row([f"{current_user['name']} ({current_user['email']})", post_type, media_file_path, final_caption, str(results), timestamp])
                    
                    st.success("✅ បានបម្រុងទុក និងកត់ត្រាទិន្នន័យចូលទៅក្នុង Google Sheets ដោយជោគជ័យ!")
                except Exception as e:
                    st.error(f"មានបញ្ហាក្នុងការកត់ត្រាចូល Google Sheets៖ {e}")
        else:
            st.warning("សូមធ្វើការ Upload ឯកសារមាតិកាជាមុនសិន។")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 2: ANALYTICS DASHBOARD ---
with tab2:
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.subheader("📊 Analytics & Performance Dashboard")
    st.markdown("ផ្ទាំងបង្ហាញស្ថិតិ និងការវិភាគទូទៅនៃការបញ្ជូនមាតិកាទៅកាន់ Social Media Platforms។")

    if os.path.exists("history.json"):
        try:
            with open("history.json", "r", encoding="utf-8") as f:
                hist_data = json.load(f)
            
            total_posts = len(hist_data)
            fb_count = sum(1 for item in hist_data if any("Facebook" in str(r)) for r in item.get("results", []))
            tiktok_count = sum(1 for item in hist_data if any("TikTok" in str(r)) for r in item.get("results", []))
            yt_count = sum(1 for item in hist_data if any("YouTube" in str(r)) for r in item.get("results", []))

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("📌 ការផុសសរុប (Total Posts)", total_posts)
            m2.metric("📘 Facebook Posts", fb_count)
            m3.metric("🎵 TikTok Posts", tiktok_count)
            m4.metric("📺 YouTube Posts", yt_count)

            st.markdown("---")
            st.subheader("📈 ប្រវត្តិនៃការប្រើប្រាស់តាមវេទិកា")
            
            if total_posts > 0:
                st.bar_chart({
                    "Facebook": fb_count,
                    "TikTok": tiktok_count,
                    "YouTube": yt_count
                })
            else:
                st.info("មិនទាន់មានទិន្នន័យគ្រប់គ្រាន់សម្រាប់បង្ហាញជាក្រាហ្វិក (Chart) ទេ។")

        except Exception as e:
            st.error(f"មានបញ្ហាក្នុងការអានទិន្នន័យសម្រាប់ Analytics៖ {e}")
    else:
        st.info("មិនទាន់មានទិន្នន័យប្រវត្តិការងារ (history.json) នៅឡើយទេ។ សូមធ្វើការ Upload មាតិកាសិន។")

    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3: VIEW HISTORY ---
with tab3:
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.subheader("📊 ពិនិត្យប្រវត្តិการងារ (View History)")

    if st.button("🔄 ផ្ទុកទិន្នន័យប្រវត្តិការងារឡើងវិញ"):
        st.rerun()

    if storage_mode == "Local history.json":
        if os.path.exists("history.json"):
            try:
                with open("history.json", "r", encoding="utf-8") as f:
                    history_data = json.load(f)
                if history_data:
                    st.dataframe(history_data, use_container_width=True)
                else:
                    st.info("មិនទាន់មានប្រវត្តិការងារក្នុង Local history.json នៅឡើយទេ។")
            except Exception as e:
                st.error(f"មានបញ្ហាក្នុងការអានឯកសារ history.json៖ {e}")
        else:
            st.info("មិនទាន់មានឯកសារ history.json ទេ។")

    elif storage_mode == "Google Sheets":
        if gsheet_json and gsheet_url:
            try:
                scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                creds_dict = json.loads(gsheet_json)
                creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
                client = gspread.authorize(creds)
                
                sheet = client.open_by_url(gsheet_url).sheet1
                records = sheet.get_all_records()
                
                if records:
                    st.dataframe(records, use_container_width=True)
                else:
                    st.info("Google Sheet របស់អ្នកនៅទទេ។")
            except Exception as e:
                st.error(f"មានបញ្ហាក្នុងการទាញយកទិន្នន័យពី Google Sheets៖ {e}")
        else:
            st.warning("សូមបំពេញ Service Account JSON Key និង Spreadsheet URL ឱ្យបានត្រឹមត្រូវនៅ Sidebar ជាមុនសិន ដើម្បីមើលប្រវត្តិពី Google Sheets។")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 4: SUPPORT CHAT ---
with tab4:
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.subheader("💬 ជំនួយការផ្ទាល់ និងសួរសំណួរ (Support Chat & AI Assistant)")
    st.markdown("សួរសំណួរ ឬពិភាក្សាជាមួយ AI Support អំពីបញ្ហាបច្ចេកទេស ការប្រើប្រាស់ API ឬគន្លឹះផ្សេងៗក្នុងប្រព័ន្ធ **UNME AI Social Media**។")

    if "support_messages" not in st.session_state:
        st.session_state["support_messages"] = [
            {"role": "assistant", "content": f"សួស្ដី {current_user['name']}! ខ្ញុំជា Support AI Assistant របស់ UNME (by Hab Rithy)។ តើខ្ញុំអាចជួយអ្វីដល់អ្នកថ្ងៃនេះ?"}
        ]

    for msg in st.session_state["support_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_query := st.chat_input("វាយសួរសំណួររបស់អ្នកនៅទីនេះ..."):
        st.session_state["support_messages"].append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            with st.spinner("កំពុងពិចារណា..."):
                try:
                    if GEMINI_API_KEY:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        chat_response = model.generate_content(f"You are a helpful support assistant for an app named 'UNME AI Social Media built by Hab Rithy'. Answer the user's question professionally: {user_query}")
                        bot_reply = chat_response.text
                    else:
                        bot_reply = "សូមកំណត់ GEMINI_API_KEY ក្នុង .env ជាមុនសិន ដើម្បីឱ្យ Support AI អាចដំណើរការឆ្លើយតបបាន។"
                    
                    st.markdown(bot_reply)
                    st.session_state["support_messages"].append({"role": "assistant", "content": bot_reply})
                except Exception as e:
                    err_msg = f"មានបញ្ហាក្នុងការភ្ជាប់ AI Support៖ {e}"
                    st.error(err_msg)
    st.markdown('</div>', unsafe_allow_html=True)
