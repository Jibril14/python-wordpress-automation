import requests
from requests.auth import HTTPBasicAuth
import base64
import requests

class WordPressClient:
    def __init__(self, base_url: str, username: str, app_password: str):
        self.base_url = base_url.rstrip("/")
        # Ensure no spaces in the password
        app_password = app_password.replace(" ", "")
        token = base64.b64encode(f"{username}:{app_password}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

    def create_post(self, title: str, content: str, media_id: int, excerpt: str, status: str = "draft") -> dict:
        url = f"{self.base_url}/wp-json/wp/v2/posts"
        payload = {
            "title": title,
            "content": content,
            "featured_media": media_id,
            "excerpt": excerpt,
            "status": status
        }
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code != 201:
            raise Exception(f"Failed to create post: {response.status_code} - {response.text}")
        return response.json()
