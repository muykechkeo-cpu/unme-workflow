import os
import requests

def upload_to_facebook(media_path, caption, post_type="🎥 Video / Reels", access_token="YOUR_FB_ACCESS_TOKEN"):
    """
    Function សម្រាប់ Upload វីដេអូ ឬ រូបភាព ទៅកាន់ Facebook Page
    """
    if not os.path.exists(media_path):
        return {"platform": "Facebook", "status": "Error", "message": "Media file not found."}

    try:
        # ប្រសិនបើជា រូបភាព (Picture / Photo Posts)
        if post_type == "🖼️ Picture / Photo Posts":
            url = "https://graph.facebook.com/v18.0/me/photos"
            files = {'source': open(media_path, 'rb')}
            data = {
                'caption': caption,
                'access_token': access_token
            }
            response = requests.post(url, files=files, data=data)
            res_json = response.json()
            
            if "id" in res_json:
                return {"platform": "Facebook", "status": "Success", "post_id": res_json["id"], "type": "Photo"}
            else:
                return {"platform": "Facebook", "status": "Failed", "details": res_json}

        # ប្រសិនបើជា វីដេអូ / Reels
        else:
            url = "https://graph.facebook.com/v18.0/me/video_reels"
            # សម្រាប់ Facebook Graph API Reels/Videos Upload ជាក់ស្តែង
            # ទីនេះប្រើប្រាស់ Mock logic ឬ Endpoint វីដេអូស្តង់ដារ
            return {"platform": "Facebook", "status": "Success", "message": "Video/Reel uploaded successfully (Mock)", "type": "Video"}

    except Exception as e:
        return {"platform": "Facebook", "status": "Error", "message": str(e)}


def upload_to_tiktok(media_path, caption, access_token="YOUR_TIKTOK_TOKEN"):
    """
    Function សម្រាប់ Upload វីដេអូទៅកាន់ TikTok Content Posting API
    """
    if not os.path.exists(media_path):
        return {"platform": "TikTok", "status": "Error", "message": "Media file not found."}

    try:
        # TikTok API integration logic here (Content Posting API / Direct Post)
        # ဥទាហរណ៍នៃការបញ្ជូនសំណើតាមរយៈ requests
        return {"platform": "TikTok", "status": "Success", "message": "Uploaded to TikTok successfully (Mock)"}
    except Exception as e:
        return {"platform": "TikTok", "status": "Error", "message": str(e)}


def upload_to_youtube(media_path, title, description, client_secret="YOUR_YT_SECRET"):
    """
    Function សម្រាប់ Upload វីដេអូទៅកាន់ YouTube Shorts / Videos
    """
    if not os.path.exists(media_path):
        return {"platform": "YouTube", "status": "Error", "message": "Media file not found."}

    try:
        # YouTube Data API v3 integration logic here
        return {"platform": "YouTube", "status": "Success", "message": "Uploaded to YouTube successfully (Mock)"}
    except Exception as e:
        return {"platform": "YouTube", "status": "Error", "message": str(e)}
