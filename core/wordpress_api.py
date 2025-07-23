import requests
from requests.auth import HTTPBasicAuth


class WordPressClient:
    def __init__(self, base_url: str, username: str, app_password: str):
        self.base_url = base_url.rstrip("/")
        self.auth = HTTPBasicAuth(username, app_password)

    def create_post(self, title: str, content: str, media_id: int, excerpt: str, status: str = "draft") -> dict:
        """
        Create a new WordPress post.
        """
        url = f"{self.base_url}/wp-json/wp/v2/posts"
        payload = {
            "title": title,
            "content": content,
            "featured_media": media_id,
            "excerpt": excerpt,
            "status": status
        }
        response = requests.post(url, json=payload, auth=self.auth)
        if response.status_code != 201:
            raise Exception(f"Failed to create post: {response.status_code} - {response.text}")
        return response.json()
