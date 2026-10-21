import os
import json
import streamlit as st
from dotenv import load_dotenv
import yt_dlp
import google.generativeai as genai
import openai
import gspread
from google.oauth2.service_account import Credentials
import datetime
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

# 1. AI Provider Selection Expander
with st.sidebar.expander("🤖 AI Provider Settings", expanded=True):
    ai_provider = st.selectbox("ជ្រើសរើសប្រភេទ AI", ["Google Gemini", "OpenAI ChatGPT"])
    
    if ai_provider == "Google Gemini":
        gemini_api_key = st.text_input("Google Gemini API Key", type="password")
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
    else:
        openai_api_key = st.text_input("OpenAI API Key", type="password")
        if openai_api_key:
            openai.api_key = openai_api_key

# 2. Google Sheets Configuration Expander
gsheet_json = ""
gsheet_url = ""
if storage_mode == "Google Sheets":
    with st.sidebar.expander("📊 Google Sheets Configuration", expanded=True):
        gsheet_json = st.text_area("Service Account JSON Key (Paste JSON text here)")
        gsheet_url = st.text_input("Spreadsheet URL / ID")

# 3. TikTok Credentials Expander
with st.sidebar.expander("🎵 TikTok Credentials", expanded=False):
    tiktok_token = st.text_input("TikTok Access Token", type="password", label_visibility="collapsed")

# 4. YouTube Credentials Expander
with st.sidebar.expander("📺 YouTube Credentials", expanded=False):
    yt_secret = st.text_input("YouTube Client Secret", type="password", label_visibility="collapsed")

# 5. Telegram Notification Settings Expander
with st.sidebar.expander("🔔 Telegram Notification Settings", expanded=False):
    tg_token = st.text_input("Telegram Bot Token", type="password")
    tg_chat_id = st.text_input("Telegram Chat ID")

# 6. Background Scheduler Settings Expander
with st.sidebar.expander("⏰ Background Scheduler Settings", expanded=False):
    schedule_freq = st.selectbox("Schedule Frequency", ["Manual", "Every 1 hour", "Every 6 hours", "Daily"], label_visibility="collapsed")

# --- MAIN INTERFACE ---
st.title("🚀 UNME Multi-Platform AI Social Media Workflow")
st.markdown("ប្រព័ន្ធគ្រប់គ្រង ស្វ័យប្រវត្តិកម្ម AI និងបញ្ជូនវីដេអូ ឬរូបភាពទៅកាន់ Facebook, TikTok និង YouTube")

# 1. Post Type & Media Input Section
st.subheader("📌 ជ្រើសរើសប្រភេទនៃការផុស (Post Type)")
post_type = st.radio(
    "តើអ្នកចង់ផុសមាតិកាប្រភេទណា?", 
    ["🎥 Video / Reels", "🖼️ Picture / Photo Posts"]
)

media_file_path = None

if post_type == "🎥 Video / Reels":
    input_method = st.radio("ជ្រើសរើសវិធីសាស្ត្របញ្ចូលវីដេអូ៖", ["Upload ឯកសារផ្ទាល់ (.mp4)", "ទាញយកពី Link (YouTube/TikTok/etc.)"])
    
    if input_method == "Upload ឯកសារផ្ទាល់ (.mp4)":
        uploaded_file = st.file_uploader("ជ្រើសរើសឯកសារវីដេអូ", type=["mp4", "mov", "avi"])
        if uploaded_file is not None:
            media_file_path = os.path.join(".", uploaded_file.name)
            with open(media_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"បានផ្ទុកឡើងវីដេអូ៖ {uploaded_file.name}")
    else:
        video_url = st.text_input("🔗 បញ្ចូល Link វីដេអូ (YouTube, TikTok, Facebook ฯលฯ):")
        if video_url and st.button("📥 ទាញយកវីដេអូ"):
            with st.spinner("កំពុងទាញយកវីដេអូតាមរយៈ yt-dlp..."):
                ydl_opts = {
                    'outtmpl': 'downloaded_video.mp4',
                    'format': 'best'
                }
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([video_url])
                    media_file_path = 'downloaded_video.mp4'
                    st.success("ទាញយកវីដេអូបានដោយជោគជ័យ!")
                except Exception as e:
                    st.error(f"មានបញ្ហាក្នុងការទាញយកវីដេអូ៖ {e}")

else:  # Picture / Photo Posts
    uploaded_image = st.file_uploader("ជ្រើសរើសរូបភាពសម្រាប់ផុស", type=["jpg", "jpeg", "png"])
    if uploaded_image is not None:
        media_file_path = os.path.join(".", uploaded_image.name)
        with open(media_file_path, "wb") as f:
            f.write(uploaded_image.getbuffer())
        st.success(f"បានផ្ទុកឡើងរូបភាព៖ {uploaded_image.name}")

# 2. AI Caption Customization & Generation
st.subheader(f"🤖 ការកំណត់ស្ទីល និងជំនួយការពី {ai_provider}")
caption_prompt = st.text_area(
    "សរសេរពាក្យបញ្ជា ឬស្ទីលដែលចង់បានឱ្យ AI បង្កើត៖",
    placeholder="ឧទាហរណ៍៖ សរសេរ Caption ជាភាសាខ្មែរឱ្យទាក់ទាញបែបកំប្លែង ព្រមទាំង Hashtags ល្បីៗ..."
)

generated_caption = ""
if st.button(f"✨ បង្កើត Caption ដោយប្រើ {ai_provider}"):
    if ai_provider == "Google Gemini":
        if 'gemini_api_key' in locals() and gemini_api_key:
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(f"Write a social media caption and hashtags based on this prompt: {caption_prompt}")
                generated_caption = response.text
                st.success("AI (Gemini) បានបង្កើត Caption រួចរាល់!")
                st.write(generated_caption)
            except Exception as e:
                st.error(f"មានកំហុសក្នុងការតភ្ជាប់ Gemini AI៖ {e}")
        else:
            st.warning("សូមបញ្ចូល Google Gemini API Key នៅ Sidebar ខាងឆ្វេងជាមុនសិន។")
    else:  # OpenAI ChatGPT
        if 'openai_api_key' in locals() and openai_api_key:
            try:
                client = openai.OpenAI(api_key=openai_api_key)
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
            st.warning("សូមបញ្ចូល OpenAI API Key នៅ Sidebar ខាងឆ្វេងជាមុនសិន។")

final_caption = st.text_area("កែសម្រួល Caption ចុងក្រោយមុនពេល Upload៖", value=generated_caption if generated_caption else caption_prompt)

# 3. Multi-Platform Selection
st.subheader("🎬 ជ្រើសរើសវេទិកាសម្រាប់ការបញ្ជូន (Multi-Platform Selection)")
col1, col2, col3 = st.columns(3)
with col1:
    pub_fb = st.checkbox("📘 Facebook", value=True)
with col2:
    pub_tiktok = st.checkbox("🎵 TikTok")
with col3:
    pub_yt = st.checkbox("📺 YouTube")

# 4. Execution Button
if st.button("🚀 ចាប់ផ្តើមដំណើរការ Upload ទៅកាន់ Platform"):
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
        
        # --- STORAGE HANDLING ---
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if storage_mode == "Local history.json":
            history_entry = {"type": post_type, "file": media_file_path, "caption": final_caption, "results": results, "time": timestamp}
            if os.path.exists("history.json"):
                with open("history.json", "r", encoding="utf-8") as f:
                    history_data = json.load(f)
            else:
                history_data = []
                
            history_data.append(history_entry)
            with open("history.json", "w", encoding="utf-8") as f:
                json.dump(history_data, f, ensure_ascii=False, indent=4)
                
            st.info("បានរក្សាទុកប្រវត្តិក្នុងប្រព័ន្ធ Local history.json រួចរាល់។")
            
        elif storage_mode == "Google Sheets":
            if gsheet_json and gsheet_url:
                try:
                    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                    creds_dict = json.loads(gsheet_json)
                    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
                    client = gspread.authorize(creds)
                    
                    sheet = client.open_by_url(gsheet_url).sheet1
                    sheet.append_row([post_type, media_file_path, final_caption, str(results), timestamp])
                    
                    st.success("បានបញ្ជូន និងកត់ត្រាទិន្នន័យចូលទៅក្នុង Google Sheets ដោយជោគជ័យ!")
                except Exception as e:
                    st.error(f"មានបញ្ហាក្នុងការកត់ត្រាចូល Google Sheets៖ {e}")
            else:
                st.warning("សូមបំពេញ Service Account JSON Key និង Spreadsheet URL ឱ្យបានត្រឹមត្រូវនៅ Sidebar ជាមុនសិន។")
    else:
        st.warning("សូមทำการ Upload ឬទាញយកឯកសារមាតិកាជាមុនសិន។")

# --- VIEW HISTORY TABLE SECTION ---
st.markdown("---")
st.subheader("📊 ពិនិត្យប្រវត្តិការងារ (View History)")

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
            st.error(f"មានបញ្ហាក្នុងការទាញយកទិន្នន័យពី Google Sheets៖ {e}")
    else:
        st.warning("សូមបំពេញ Service Account JSON Key និង Spreadsheet URL នៅ Sidebar ជាមុនសិន ដើម្បីមើលប្រវត្តិពី Google Sheets។")
