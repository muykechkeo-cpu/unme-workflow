import os
import json
import time
import cv2
import yt_dlp
import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
import google.generativeai as genai
from dotenv import load_dotenv
from multi_platform import upload_to_youtube, upload_to_tiktok

# ផ្ទុកទិន្នន័យពីឯកសារ .env
load_dotenv()

VIDEO_DIR = r"D:\fb_ai_workflow\videos"
UPLOADED_DIR = r"D:\fb_ai_workflow\uploaded"
HISTORY_FILE = r"D:\fb_ai_workflow\history.json"

# Google Sheets Configuration
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "YOUR_GOOGLE_SHEET_ID")
CREDENTIALS_FILE = r"D:\fb_ai_workflow\credentials.json"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# 🔍 មុខងារពិនិត្យវីដេអូមុនពេលបង្ហោះ (Pre-Flight Video Validation)
def validate_video_preflight(video_path, max_size_mb=500):
    issues = []
    if not os.path.exists(video_path):
        return False, ["រកមិនឃើញឯកសារវីដេអូនេះទេ។"]
    
    file_size_bytes = os.path.getsize(video_path)
    file_size_mb = file_size_bytes / (1024 * 1024)
    if file_size_mb > max_size_mb:
        issues.append(f"ទំហំဖိုင်ធំពេក ({file_size_mb:.2f} MB) ដែលហួសកម្រិតកំណត់ {max_size_mb} MB។")
        
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return False, ["មិនអាចអានទិន្នន័យវីដេអូ (Video codec error) បានទេ។"]
            
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        cap.release()
        
        if width <= 0 or height <= 0:
            issues.append("Resolution វីដេអូមិនត្រឹមត្រូវ។")
        if duration < 1:
            issues.append("វីដេអូខ្លីពេក (តិចជាង ១ វិនាទី)។")
    except Exception as e:
        issues.append(f"បញ្ហាពេលពិនិត្យ Video Metadata: {e}")
        
    if issues:
        return False, issues
    return True, ["វីដេអូមានលក្ខណៈសម្បត្តិគ្រប់គ្រាន់ និងត្រឹមត្រូវ។"]

def add_watermark_cv2(input_path, output_path, watermark_text="@UNME_Official"):
    try:
        cap = cv2.VideoCapture(input_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            cv2.putText(
                frame, watermark_text, (width - 320, height - 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA
            )
            out.write(frame)

        cap.release()
        out.release()
        return True
    except Exception as e:
        print(f"OpenCV Watermark Error: {e}")
        return False

def download_video_from_link(video_url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(VIDEO_DIR, '%(id)s.%(ext)s'),
        'restrictfilenames': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info_dict)
            return filename
    except Exception as e:
        print(f"❌ Error downloading video: {e}")
        return None

# 📊 Google Sheets Functions
def get_google_sheet_table():
    try:
        if not os.path.exists(CREDENTIALS_FILE) or GOOGLE_SHEET_ID == "YOUR_GOOGLE_SHEET_ID":
            return []
        
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
        client = gspread.authorize(creds)
        
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
        records = sheet.get_all_records()
        return records
    except Exception as e:
        print(f"Google Sheets Read Error: {e}")
        return []

def mark_as_uploaded_gsheets(video_name, platforms=[]):
    try:
        if not os.path.exists(CREDENTIALS_FILE) or GOOGLE_SHEET_ID == "YOUR_GOOGLE_SHEET_ID":
            return False
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        platforms_str = ", ".join(platforms)
        sheet.append_row([video_name, timestamp, platforms_str])
        return True
    except Exception as e:
        print(f"Google Sheets Write Error: {e}")
        return False

# 📂 Local history.json Functions
def get_local_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            uploaded_list = data.get("uploaded_videos", [])
            formatted = []
            for item in uploaded_list:
                if isinstance(item, dict):
                    formatted.append({
                        "Filename": item.get("filename"),
                        "Timestamp": item.get("timestamp"),
                        "Platforms": ", ".join(item.get("platforms", []))
                    })
                elif isinstance(item, str):
                    formatted.append({
                        "Filename": item,
                        "Timestamp": "N/A",
                        "Platforms": "N/A"
                    })
            return formatted
    except:
        return []

def mark_as_uploaded_local(video_name, platforms=[]):
    data = {"uploaded_videos": []}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            pass
    
    entry = {
        "filename": video_name,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "platforms": platforms
    }
    
    if "uploaded_videos" not in data:
        data["uploaded_videos"] = []
        
    data["uploaded_videos"] = [item for item in data["uploaded_videos"] if (item.get("filename") if isinstance(item, dict) else item) != video_name]
    data["uploaded_videos"].append(entry)
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def check_if_uploaded(video_name, storage_mode):
    if storage_mode == "Google Sheets":
        records = get_google_sheet_table()
        for row in records:
            if row.get("Filename") == video_name or row.get("ឈ្មោះវីដេអូ") == video_name:
                return True
        return False
    else:
        records = get_local_history()
        for row in records:
            if row.get("Filename") == video_name:
                return True
        return False

def mark_as_uploaded(video_name, platforms, storage_mode):
    if storage_mode == "Google Sheets":
        mark_as_uploaded_gsheets(video_name, platforms)
    else:
        mark_as_uploaded_local(video_name, platforms)

def send_telegram_notification(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

# 🧠 មុខងារវិភាគ Facebook Page Competitor
def analyze_competitor_page(page_id, access_token, gemini_api_key):
    if not page_id or not access_token:
        return ["សូមបញ្ចូល Facebook Page ID និង Access Token ជាមុនសិន។"]
    url = f"https://graph.facebook.com/v18.0/{page_id}/posts"
    params = {'access_token': access_token, 'fields': 'message,created_time,shares,comments.summary(true),likes.summary(true)', 'limit': 5}
    try:
        response = requests.get(url, params=params, timeout=10).json()
        if 'error' in response:
            return [f"Facebook API Error: {response['error']['message']}"]
        posts_data = response.get('data', [])
        if not posts_data:
            return ["រកមិនឃើញទិន្នន័យ Posts ពី Page នេះទេ។"]
        posts_text = ""
        for idx, post in enumerate(posts_data, 1):
            msg = post.get('message', 'គ្មានអត្ថបទ')
            posts_text += f"\n--- Post {idx} ---\n{msg}\n"
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-3.8-flash')
            prompt = f"ផ្អែកលើមាតិកា និង Caption នៃ Posts ខាងក្រោមពី Facebook Page ប្រភពដើម សូមជួយវិភាគរកមើល Trend និងបង្កើត Idea វីដេអូខ្លីៗ (Shorts/Reels) ចំនួន ៣ ដែលមានភាពទាក់ទាញខ្លាំងជាភាសាខ្មែរ៖\n{posts_text}"
            return [model.generate_content(prompt).text]
        else:
            return ["Gemini API Key មិនទាន់បានកំណត់។"]
    except Exception as e:
        return [f"Error fetching page content: {e}"]

# 🧠 មុខងារវិភាគ TikTok Creator
def analyze_tiktok_creator(tiktok_username, gemini_api_key):
    if not tiktok_username:
        return ["សូមបញ្ចូល TikTok Username ឬ ID គោលដៅជាមុនសិន។"]
    ydl_opts = {'extract_flat': True, 'playlistend': 5}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.tiktok.com/@{tiktok_username}", download=False)
            entries = info.get('entries', [])
            tiktok_texts = ""
            for idx, entry in enumerate(entries[:5], 1):
                title = entry.get('title', 'គ្មានចំណងជើង')
                tiktok_texts += f"\n--- TikTok Video {idx} ---\n{title}\n"
        if gemini_api_key and tiktok_texts:
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-3.8-flash')
            prompt = f"ផ្អែកលើចំណងជើងវីដេអូ TikTok ទាំងនេះពី Creator គោលដៅ សូមជួយវិភាគរក Trend និងបង្កើត Idea វីដេអូខ្លីៗ (TikTok Trends/Reels) ចំនួន ៣ ដែលទាក់ទាញខ្លាំងជាភាសាខ្មែរ៖\n{tiktok_texts}"
            return [model.generate_content(prompt).text]
        else:
            return ["រកមិនឃើញទិន្នន័យវីដេអូ ឬ Gemini API Key មិនទាន់បានកំណត់។"]
    except Exception as e:
        return [f"Error fetching TikTok content: {e}"]

# 🧠 មុខងារវិភាគ YouTube Channel
def analyze_youtube_channel(channel_url, gemini_api_key):
    if not channel_url:
        return ["សូមបញ្ចូល YouTube Channel ID ឬ URL គោលដៅជាមុនសិន។"]
    ydl_opts = {'extract_flat': True, 'playlistend': 5}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
            entries = info.get('entries', [])
            yt_texts = ""
            for idx, entry in enumerate(entries[:5], 1):
                title = entry.get('title', 'គ្មានចំណងជើង')
                yt_texts += f"\n--- YouTube Video {idx} ---\n{title}\n"
        if gemini_api_key and yt_texts:
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-3.8-flash')
            prompt = f"ផ្អែកលើចំណងជើងវីដេអូនានាពី YouTube Channel គោលដៅ សូមជួយវិភាគរក Trend និងបង្កើត Idea វីដេអូ Shorts ថ្មីៗចំនួន ៣ ដែលមានភាពទាក់ទាញខ្លាំងជាភាសាខ្មែរ៖\n{yt_texts}"
            return [model.generate_content(prompt).text]
        else:
            return ["រកមិនឃើញទិន្នន័យវីដេអូ ឬ Gemini API Key មិនទាន់បានកំណត់។"]
    except Exception as e:
        return [f"Error fetching YouTube content: {e}"]

def upload_with_retry(video_path, target_file, ai_caption, publish_fb, publish_tiktok, publish_yt, max_retries=3):
    is_valid, validation_messages = validate_video_preflight(video_path)
    if not is_valid:
        return [], validation_messages

    success_platforms = []
    error_messages = []
    
    processed_video_path = video_path.replace(".mp4", "_wm.mp4")
    watermark_success = add_watermark_cv2(video_path, processed_video_path, watermark_text="@UNME_Official")
    upload_target_path = processed_video_path if watermark_success else video_path

    for attempt in range(1, max_retries + 1):
        success_platforms = []
        error_messages = []
        
        if publish_fb:
            url = f"https://graph-video.facebook.com/v18.0/{PAGE_ID}/videos"
            data = {'access_token': ACCESS_TOKEN, 'description': ai_caption}
            try:
                with open(upload_target_path, 'rb') as vf:
                    res = requests.post(url, data=data, files={'source': vf}, timeout=600).json()
                    if 'error' in res:
                        error_messages.append(f"Facebook: {res['error']['message']}")
                    else:
                        success_platforms.append("Facebook Reels")
            except Exception as e:
                error_messages.append(f"Facebook Exception: {e}")

        if publish_tiktok and TIKTOK_ACCESS_TOKEN:
            try:
                upload_to_tiktok(upload_target_path, ai_caption)
                success_platforms.append("TikTok")
            except Exception as e:
                error_messages.append(f"TikTok Exception: {e}")

        if publish_yt and YOUTUBE_API_KEY:
            try:
                upload_to_youtube(upload_target_path, target_file, ai_caption)
                success_platforms.append("YouTube Shorts")
            except Exception as e:
                error_messages.append(f"YouTube Exception: {e}")
        
        if not error_messages:
            break
        else:
            time.sleep(10)
            
    if os.path.exists(processed_video_path):
        try:
            os.remove(processed_video_path)
        except:
            pass

    return success_platforms, error_messages

st.set_page_config(page_title="UNME Multi-Platform AI Workflow", page_icon="🚀", layout="wide")

st.title("🚀 UNME Multi-Platform AI Social Media Workflow")
st.markdown("ប្រព័ន្ធគ្រប់គ្រង និងបង្ហោះវីដេអូស្វ័យប្រវត្តិទៅកាន់ Facebook, TikTok និង YouTube")

st.sidebar.header("⚙️ System Configuration")
with st.sidebar.expander("📂 History Storage Mode"):
    storage_mode = st.radio("ជ្រើសរើសទម្រង់ប្រវត្តិសកម្មភាព:", ["Google Sheets", "history.json (Local)"])

with st.sidebar.expander("🔑 API Credentials (.env)"):
    GEMINI_API_KEY = st.text_input("Gemini API Key", type="password", value=GEMINI_API_KEY or "")
    PAGE_ID = st.text_input("Facebook Page ID", value=PAGE_ID or "")
    ACCESS_TOKEN = st.text_input("Facebook Access Token", type="password", value=ACCESS_TOKEN or "")

if storage_mode == "Google Sheets":
    with st.sidebar.expander("📊 Google Sheets Configuration"):
        GOOGLE_SHEET_ID = st.text_input("Google Sheet ID", value=GOOGLE_SHEET_ID if GOOGLE_SHEET_ID != "YOUR_GOOGLE_SHEET_ID" else "")

with st.sidebar.expander("🎵 TikTok Credentials"):
    TIKTOK_ACCESS_TOKEN = st.text_input("TikTok Access Token", type="password", value=TIKTOK_ACCESS_TOKEN or "")

with st.sidebar.expander("▶️ YouTube Credentials"):
    YOUTUBE_API_KEY = st.text_input("YouTube API Key / OAuth Token", type="password", value=YOUTUBE_API_KEY or "")

with st.sidebar.expander("🔔 Telegram Notification Settings"):
    TELEGRAM_BOT_TOKEN = st.text_input("Telegram Bot Token", type="password", value=TELEGRAM_BOT_TOKEN or "")
    TELEGRAM_CHAT_ID = st.text_input("Telegram Chat ID", value=TELEGRAM_CHAT_ID or "")

with st.sidebar.expander("⏰ Background Scheduler Settings"):
    enable_scheduler = st.checkbox("បើកដំណើរការ Background Scheduler", value=False)
    schedule_mode = st.radio("ជ្រើសរើសទម្រង់កំណត់ពេល:", ["ចន្លោះពេល (Interval)", "ម៉ោងជាក់លាក់ (Daily Time)"])
    if schedule_mode == "ចន្លោះពេល (Interval)":
        interval_hours = st.number_input("បង្ហោះរៀងរាល់ប៉ុន្មានម៉ោង?", min_value=1, max_value=24, value=2)
    else:
        scheduled_time = st.text_input("កំណត់ម៉ោងបង្ហោះ (ឧទាហរណ៍ 08:30)", value="08:30")

st.sidebar.markdown("---")
menu = st.sidebar.selectbox("ជ្រើសរើសមុខងារ", [
    "📤 បញ្ចូល និងបង្ហោះវីដេអូ", 
    "⏰ គ្រប់គ្រងកាលវិភាគ (Scheduler)", 
    "📜 ประวัติសកម្មភាព (History & Logs)", 
    "📊 ពិនិត្យស្ថិតិ Insights", 
    "💬 ឆ្លើយតប Comment ស្វ័យប្រវត្តិ"
])

if menu == "📤 បញ្ចូល និងបង្ហោះវីដេអូ":
    st.header("📤 បញ្ចូលវីដេអូថ្មី និងបង្ហោះទៅកាន់បណ្តាញសង្គម")
    main_col, side_col = st.columns([2, 1])
    
    with main_col:
        with st.expander("📥 ទាញយកវីដេអូពី Link ដាក់ចូល Queue ស្វ័យប្រវត្តិ"):
            url_input = st.text_input("បញ្ចូលតំណភ្ជាប់វីដេអូ (YouTube, TikTok, Facebook Link):")
            if st.button("⬇️ ទាញយកវីដេអូ (Download)"):
                if url_input:
                    with st.spinner("⏳ កំពុងទាញយកវីដេអូតាមរយៈ yt-dlp..."):
                        downloaded_file = download_video_from_link(url_input)
                        if downloaded_file:
                            st.success(f"✅ ទាញយកវីដេអូជោគជ័យ និងបានដាក់ចូល Queue រួចរាល់!")
                            st.rerun()
                        else:
                            st.error("❌ មានបញ្ហាក្នុងការទាញយកវីដេអូ សូមពិនិត្យ Link ឡើងវិញ។")
                else:
                    st.warning("⚠️ សូមបញ្ចូលតំណភ្ជាប់វីដេអូជាមុនសិន។")

        uploaded_file = st.file_uploader("ជ្រើសរើសឯកសារវីដេអូផ្ទាល់ (.mp4)", type=["mp4"])
        if uploaded_file is not None:
            save_path = os.path.join(VIDEO_DIR, uploaded_file.name)
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"✅ បានរក្សាទុកវីដេអូ '{uploaded_file.name}' ចូលក្នុងថត `videos` រួចរាល់!")
            st.rerun()
            
        st.markdown("---")
        st.subheader("🤖 ការកំណត់ស្ទីល AI Caption (សរសេរបញ្ជាដោយសេរី)")
        custom_prompt_style = st.text_area(
            "សរសេរព័ត៌មាន ឬស្ទីលដែលចង់ឱ្យ AI បង្កើត៖",
            value="សរសេរ Caption ជាភាសាខ្មែរឱ្យទាក់ទាញខ្លាំង ព្រមទាំងដាក់ Hashtags ល្អៗ。"
        )

        st.markdown("---")
        st.subheader("🎬 ជ្រើសរើសវេទិកាសម្រាប់បង្ហោះ (Multi-Platform Selection)")
        col1, col2, col3 = st.columns(3)
        publish_fb = col1.checkbox("📘 Facebook Reels", value=True)
        publish_tiktok = col2.checkbox("🎵 TikTok", value=False)
        publish_yt = col3.checkbox("▶️ YouTube Shorts", value=False)
        
        st.markdown("---")
        if os.path.exists(VIDEO_DIR):
            videos = [f for f in os.listdir(VIDEO_DIR) if f.lower().endswith('.mp4')]
        else:
            videos = []

        if videos:
            if st.button("🚀 ចាប់ផ្តើមបង្ហោះវីដេអូទី ១ ទៅកាន់ Platforms ដែលបានជ្រើសរើស"):
                target_file = videos[0]
                video_path = os.path.join(VIDEO_DIR, target_file)
                
                with st.spinner("🤖 កំពុងឱ្យ Gemini AI ជួយសរសេរ Caption..."):
                    try:
                        model = genai.GenerativeModel('gemini-3.8-flash')
                        prompt = f"វីដេអូមានឈ្មោះថា៖ '{target_file}'. បញ្ជាបន្ថែម៖ {custom_prompt_style}"
                        ai_caption = model.generate_content(prompt).text
                    except:
                        ai_caption = "មាតិកាវីដេអូអប់រំ និងកម្សាន្ត #Reels #UNME"
                
                with st.spinner("🔄 កំពុងពិនិត្យគុណភាព (Pre-Flight), ដាក់ Watermark និងបង្ហោះ..."):
                    success_platforms, error_messages = upload_with_retry(
                        video_path, target_file, ai_caption, publish_fb, publish_tiktok, publish_yt
                    )

                if error_messages and not success_platforms:
                    st.error(f"❌ ការបង្ហោះបរាជ័យដោយសារបញ្ហា៖ {', '.join(error_messages)}")
                else:
                    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                        if success_platforms:
                            send_telegram_notification(f"🚀 **បង្ហោះវីដេអូជោគជ័យ!**\n📹 ឈ្មោះ៖ `{target_file}`\n🌐 Platforms: {', '.join(success_platforms)}")
                        if error_messages:
                            send_telegram_notification(f"❌ **មានបញ្ហាខកខានខ្លះ!**\n📹 ឈ្មោះ៖ `{target_file}`\n⚠️ Errors: {', '.join(error_messages)}")

                    mark_as_uploaded(target_file, success_platforms, storage_mode)
                    if os.path.exists(video_path):
                        os.rename(video_path, os.path.join(UPLOADED_DIR, target_file))
                    
                    st.success("🎉 ការដំណើរការបង្ហោះបានបញ្ចប់សព្វគ្រប់!")
                    st.rerun()

    with side_col:
        st.markdown("### 🎬 វីដេអូរង់ចាំបង្ហោះ (Queue)")
        if os.path.exists(VIDEO_DIR):
            queue_videos = [f for f in os.listdir(VIDEO_DIR) if f.lower().endswith('.mp4')]
        else:
            queue_videos = []

        if not queue_videos:
            st.info("📭 មិនទាន់មានវីដេអូរង់ចាំទេ។")
        else:
            for v in queue_videos:
                if check_if_uploaded(v, storage_mode):
                    st.warning(f"📹 {v} (⚠️ ធ្លាប់បានបង្ហោះ)")
                else:
                    st.success(f"📹 {v} (✨ ថ្មី)")

elif menu == "⏰ គ្រប់គ្រងកាលវិភាគ (Scheduler)":
    st.header("⏰ គ្រប់គ្រង និងតាមដានកាលវិភាគបង្ហោះវីដេអូស្វ័យប្រវត្តិ")
    if enable_scheduler:
        st.success("✅ Background Scheduler កំពុងដំណើរការ!")
        st.write(f"- **ទម្រង់:** {schedule_mode}")
    else:
        st.warning("⚠️ Scheduler មិនទាន់ត្រូវបានបើកដំណើរការទេ។")

elif menu == "📜 ประวัติសកម្មភាព (History & Logs)":
    st.header(f"📜 ប្រវត្តិកំណត់ត្រាសកម្មភាពបង្ហោះវីដេអូ ({storage_mode})")
    if storage_mode == "Google Sheets":
        records = get_google_sheet_table()
    else:
        records = get_local_history()

    if records:
        st.dataframe(records, use_container_width=True)
    else:
        st.info(f"📭 មិនទាន់មានទិន្នន័យនៅក្នុង {storage_mode} ទេ។")

elif menu == "📊 ពិនិត្យស្ថិតិ Insights":
    st.header("📊 ស្ថិតិស៊ីជម្រៅ និង AI Multi-Platform Polling (Content Ideas)")
    tab1, tab2 = st.tabs(["📊 Platform Insights", "🧠 AI Competitor / Multi-Platform Polling"])
    
    with tab1:
        st.subheader("ស្ថិតិទូទៅពីប្រព័ន្ធ")
        st.success("ទិន្នន័យស្ថិតិដំណើរការធម្មតា។")
        
    with tab2:
        st.subheader("🧠 ស្កេនប្រភពដើមពី Facebook, TikTok ឬ YouTube ដើម្បីបង្កើត Idea វីដេអូថ្មី")
        selected_platform = st.selectbox(
            "ជ្រើសរើសវេទិកាប្រភពដើម (Source Platform):",
            ["📘 Facebook Page", "🎵 TikTok Creator", "▶️ YouTube Channel"]
        )
        
        if selected_platform == "📘 Facebook Page":
            input_label = "បញ្ចូល Facebook Page ID គោលដៅ:"
            default_val = PAGE_ID or ""
        elif selected_platform == "🎵 TikTok Creator":
            input_label = "បញ្ចូល TikTok Username ឬ ID គោលដៅ:"
            default_val = ""
        else:
            input_label = "បញ្ចូល YouTube Channel ID ឬ URL គោលដៅ:"
            default_val = ""
            
        target_id = st.text_input(input_label, value=default_val)
        
        if st.button(f"🚀 ស្កេន {selected_platform} និងទាញយក Idea"):
            with st.spinner(f"⏳ កំពុងទាញយកទិន្នន័យពី {selected_platform} និងឱ្យ Gemini AI វិភាគ..."):
                if selected_platform == "📘 Facebook Page":
                    ideas = analyze_competitor_page(target_id, ACCESS_TOKEN, GEMINI_API_KEY)
                elif selected_platform == "🎵 TikTok Creator":
                    ideas = analyze_tiktok_creator(target_id, GEMINI_API_KEY)
                else:
                    ideas = analyze_youtube_channel(target_id, GEMINI_API_KEY)
                    
                st.markdown(f"### 💡 លទ្ធផលវិភាគ Idea ពី {selected_platform}៖")
                for idea in ideas:
                    st.info(idea)

elif menu == "💬 ឆ្លើយតប Comment ស្វ័យប្រវត្តិ":
    st.header("💬 ប្រព័ន្ធឆ្លើយតប Comment ស្វ័យប្រវត្តិដោយ AI")
    if st.button("🤖 ដំណើរការឆ្លើយតប Comments"):
        st.info("កំពុងពិនិត្យ Comments...")