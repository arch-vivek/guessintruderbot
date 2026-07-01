import requests
from config import BOT_TOKEN

def get_user_profile_photo_url(user_id: int) -> str:
    """Return the URL of the user's highest‑resolution profile photo, or an empty string."""
    try:
        # Get user profile photos
        resp = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getUserProfilePhotos",
            params={"user_id": user_id, "limit": 1}
        ).json()
        if not resp.get("ok") or not resp["result"]["photos"]:
            return ""
        # Get the largest version of the first photo
        photo_sizes = resp["result"]["photos"][0]
        largest = photo_sizes[-1]  # last element is highest resolution
        file_id = largest["file_id"]
        # Get file path
        file_resp = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getFile",
            params={"file_id": file_id}
        ).json()
        if not file_resp.get("ok"):
            return ""
        file_path = file_resp["result"]["file_path"]
        return f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    except:
        return ""

# Simple cache to avoid hitting API every page load
_photo_cache = {}

def get_cached_photo_url(user_id: int) -> str:
    if user_id not in _photo_cache:
        _photo_cache[user_id] = get_user_profile_photo_url(user_id)
    return _photo_cache[user_id]