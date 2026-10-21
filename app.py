import os
import json
import streamlit as st
from dotenv import load_dotenv
import yt_dlp
import google.generativeai as genai
from multi_platform import upload_to_youtube, upload_to_tiktok, upload_to_facebook

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="UNME Multi-Platform AI Workflow",
    page_icon="🚀",
    layout="wide"
)

# --- SIDEBAR CONFIGURATION ---
st.sidebar.title("⚙️ System Configuration")

storage_mode = st.sidebar.selectbox(
    "📁 History Storage Mode",
    ["Local history.json", "Google Sheets"]
)

st.sidebar.markdown("---")
gemini_api_key = st.sidebar.text_input("🔑 Google Gemini API Key", type="password")

if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

if storage_mode == "Google Sheets":
    st.sidebar.subheader("📊 Google Sheets Configuration")
    gsheet_json = st.sidebar.text_input("Service Account JSON Key (or Path)", type="password")
    gsheet_url = st.sidebar.text_input("Spreadsheet URL / ID")

st.sidebar.subheader("🎵 TikTok Credentials")
tiktok_token = st.sidebar.text_input("TikTok Access Token", type="password")

st.sidebar.subheader("📺 YouTube Credentials")
yt_secret = st.sidebar.text_input("YouTube Client Secret", type="password")

st.sidebar.subheader("🔔 Telegram Notification Settings")
tg_token = st.sidebar.text_input("Telegram Bot Token", type="password")
tg_chat_id = st.sidebar.text_input("Telegram Chat ID")

st.sidebar.subheader("⏰ Background Scheduler Settings")
schedule_freq = st.sidebar.selectbox("Schedule Frequency", ["Manual", "Every 1 hour", "Every 6 hours", "Daily"])

# --- MAIN INTERFACE ---
st.title("🚀 UNME Multi-Platform AI Social Media Workflow")
st.markdown("ប្រព័ន្ធគ្រប់គ្រង ស្វ័យប្រវត្តិកម្ម AI និងបញ្ជូនវីដេអូទៅកាន់ Facebook, TikTok និង YouTube")

# 1. Video Input Section (Upload or Download via Link)
st.subheader("📥 បញ្ចូលវីដេអូ ឬទាញយកតាម Link")
input_method = st.radio("ជ្រើសរើសវិធីសាស្ត្របញ្ចូលវីដេអូ៖", ["Upload ឯកសារផ្ទាល់ (.mp4)", "ទាញយកពី Link (YouTube/TikTok/etc.)"])

video_file_path = None

if input_method == "Upload ឯកសារផ្ទាល់ (.mp4)":
    uploaded_file = st.file_uploader("ជ្រើសរើសឯកសារវីដេអូ", type=["mp4", "mov", "avi"])
    if uploaded_file is not None:
        video_file_path = os.path.join(".", uploaded_file.name)
        with open(video_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"បានផ្ទុកឡើងវីដេអូ៖ {uploaded_file.name}")
else:
    video_url = st.text_input("🔗 បញ្ចូល Link វីដេអូ (YouTube, TikTok, Facebook ฯลฯ):")
    if video_url and st.button("📥 ទាញយកវីដេអូ"):
        with st.spinner("កំពុងទាញយកវីដេអូតាមរយៈ yt-dlp..."):
            ydl_opts = {
                'outtmpl': 'downloaded_video.mp4',
                'format': 'best'
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video_url])
                video_file_path = 'downloaded_video.mp4'
                st.success("ទាញយកវីដេអូបានដោយជោគជ័យ!")
            except Exception as e:
                st.error(f"មានបញ្ហាក្នុងការទាញយកវីដេអូ៖ {e}")

# 2. AI Caption Customization & Generation
st.subheader("🤖 ការកំណត់ស្ទីល និងជំនួយការពី AI Caption")
caption_prompt = st.text_area(
    "សរសេរពាក្យបញ្ជា ឬស្ទីលដែលចង់បានឱ្យ AI បង្កើត៖",
    placeholder="ឧទាហរណ៍៖ សរសេរ Caption ជាភាសាខ្មែរឱ្យទាក់ទាញបែបកំប្លែង ព្រមទាំង Hashtags ល្បីៗ..."
)

generated_caption = ""
if st.button("✨ បង្កើត Caption ដោយប្រើ Gemini AI"):
    if gemini_api_key:
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(f"Write a social media caption and hashtags based on this prompt: {caption_prompt}")
            generated_caption = response.text
            st.success("AI បានបង្កើត Caption រួចរាល់!")
            st.write(generated_caption)
        except Exception as e:
            st.error(f"មានកំហុសក្នុងការតភ្ជាប់ Gemini AI៖ {e}")
    else:
        st.warning("សូមបញ្ចូល Google Gemini API Key នៅ Sidebar ខាងឆ្វេងជាមុនសិន។")

final_caption = st.text_area("កែសម្រួល Caption ចុងក្រោយមុនពេល Upload៖", value=generated_caption if generated_caption else caption_prompt)

# 3. Multi-Platform Selection
st.subheader("🎬 ជ្រើសរើសវេទិកាសម្រាប់ការបញ្ជូន (Multi-Platform Selection)")
col1, col2, col3 = st.columns(3)
with col1:
    pub_fb = st.checkbox("📘 Facebook Reels", value=True)
with col2:
    pub_tiktok = st.checkbox("🎵 TikTok")
with col3:
    pub_yt = st.checkbox("📺 YouTube Shorts")

# 4. Execution Button
if st.button("🚀 ចាប់ផ្តើមដំណើរការ Upload ទៅកាន់ Platform"):
    if video_file_path and os.path.exists(video_file_path):
        st.info("ប្រព័ន្ធកំពុងដំណើរការបញ្ជូនវីដេអូ...")
        results = []
        
        if pub_fb:
            res_fb = upload_to_facebook(video_file_path, final_caption)
            results.append(res_fb)
        if pub_tiktok:
            res_tk = upload_to_tiktok(video_file_path, final_caption)
            results.append(res_tk)
        if pub_yt:
            res_yt = upload_to_youtube(video_file_path, "AI Generated Video", final_caption)
            results.append(res_yt)
            
        st.success("ការបញ្ជូនបានបញ្ចប់!")
        st.json(results)
        
        # Save to local history.json mode
        history_entry = {"file": video_file_path, "caption": final_caption, "results": results}
        if os.path.exists("history.json"):
            with open("history.json", "r", encoding="utf-8") as f:
                history_data = json.load(f)
        else:
            history_data = []
            
        history_data.append(history_entry)
        with open("history.json", "w", encoding="utf-8") as f:
            json.dump(history_data, f, ensure_ascii=False, indent=4)
            
        st.info("បានរក្សាទុកប្រវត្តិក្នុងប្រព័ន្ធ Local history.json រួចរាល់។")
    else:
        st.warning("សូមทำการ Upload វីដេអូ ឬទាញយកវីដេអូតាម Link ជាមុនសិន។")
