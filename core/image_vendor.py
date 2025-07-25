import os
import requests
from io import BytesIO
from base64 import b64encode
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from templates.article_outline import STRING_SIX
from .logger import log_event

load_dotenv()

wordpress_url = os.getenv("WORDPRESS_URL")
wordpress_username = os.getenv("WORDPRESS_USERNAME")
wordpress_app_password = os.getenv("WORDPRESS_APP_PASSWORD")
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_model = os.getenv("OPENAI_MODEL")
pexels_api_key =  os.getenv("PEXELS_API_KEY")
unsplash_api_key =  os.getenv("UNSPLASH_ACCESS_KEY")
pixabay_api_key =  os.getenv("PIXABAY_API_KEY")
freepik_api_key = os.getenv("FREEPIK_API_KEY")

class ImageIntegrationBot:
    def __init__(self, wp_url, wp_user, wp_pass, api_keys):
        self.wp_url = wp_url.rstrip("/")
        token = b64encode(f"{wp_user}:{wp_pass}".encode())
        self.wp_headers = {
            "Authorization": f"Basic {token.decode('utf-8')}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        self.api_keys = api_keys

    def generate_keyword(self, title, section):
        llm = ChatOpenAI(
            model=openai_model,
            temperature=0.7,
            api_key=openai_api_key
        )
        prompt_template = PromptTemplate.from_template("{prompt}")
        chain = prompt_template | llm
        full_prompt = f"""
        Blog Title: {title}
        Section: {section}

        {STRING_SIX}
        """
        try:
            result = chain.invoke({"prompt": full_prompt})
            return result.content
        except Exception as e:
            return None

    def search_pexels(self, query):
        try:
            url = f"https://api.pexels.com/v1/search?query={query}"
            r = requests.get(url, headers={"Authorization": self.api_keys['pexels']})
            r.raise_for_status()
            data = r.json()
            if data['photos']:
                img = data['photos'][0]
                return img['src']['large'], f"Photo by {img['photographer']} on Pexels"
        except Exception as e:
            log_event("ERROR", f"Couldn't use image from this vendor: {e}") 
        return None

    def search_unsplash(self, query):
        try:
            url = f"https://api.unsplash.com/search/photos?query={query}&client_id={self.api_keys['unsplash']}"
            r = requests.get(url)
            r.raise_for_status()
            data = r.json()
            if data['results']:
                img = data['results'][0]
                return img['urls']['regular'], f"Photo by {img['user']['name']} on Unsplash"
        except Exception as e:
            log_event("ERROR", f"Couldn't use image from this vendor: {e}") 
        return None

    def search_pixabay(self, query):
        try:
            url = f"https://pixabay.com/api/?key={self.api_keys['pixabay']}&q={query}"
            r = requests.get(url)
            r.raise_for_status()
            data = r.json()
            if data['hits']:
                img = data['hits'][0]
                return img['largeImageURL'], f"Image by {img['user']} from Pixabay"
        except Exception as e:
            log_event("ERROR", f"Couldn't use image from this vendor: {e}") 
        return None
    
    def search_freepik(self, query):
        try:
            headers = {
                "x-freepik-api-key": self.api_keys['freepik']
            }

            search_url = "https://api.freepik.com/v1/resources"
            params = {
                "search": query,
                "limit": 5  # Get a few so we can filter
            }
            r = requests.get(search_url, headers=headers, params=params)
            r.raise_for_status()
            data = r.json()

            if not data.get("data"):
                return None

            for item in data["data"]:
                resource_id = item["id"]
                title = item.get("title", "Freepik image")
                author_name = item.get("author", {}).get("name", "")

                download_url = f"https://api.freepik.com/v1/resources/{resource_id}/download"
                dl = requests.get(download_url, headers=headers)
                dl.raise_for_status()
                dl_data = dl.json()
                img_url = dl_data["data"]["url"]

                if img_url.lower().endswith((".jpg", ".jpeg", ".png")):
                    attribution = f"{title} by {author_name} on Freepik"
                    return img_url, attribution

            # I.e, no valid JPG/PNG found
            return None

        except Exception as e:
            log_event("ERROR", f"Couldn't use image from this vendor: {e}") 
            return None

    def search_wikimedia(self, query):
        try:
            headers = {
                "User-Agent": f"WPImageBot/1.0 ({self.wp_url}/contact)"
            }

            search_url = "https://commons.wikimedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": query,
                "srnamespace": 6,
                "srlimit": 5
            }
            r = requests.get(search_url, params=params, headers=headers)
            r.raise_for_status()
            data = r.json()

            if not data['query']['search']:
                return None

            for result in data['query']['search']:
                file_title = result['title']

                imageinfo_url = "https://commons.wikimedia.org/w/api.php"
                params = {
                    "action": "query",
                    "format": "json",
                    "titles": file_title,
                    "prop": "imageinfo",
                    "iiprop": "url|mime"
                }
                img_req = requests.get(imageinfo_url, params=params, headers=headers)
                img_req.raise_for_status()
                image_data = img_req.json()

                pages = image_data["query"]["pages"]
                for page in pages.values():
                    if "imageinfo" in page:
                        info = page["imageinfo"][0]
                        mime = info.get("mime", "")
                        if mime.startswith("image/"):
                            img_url = info["url"]
                            return img_url, f"Image from Wikimedia Commons ({file_title})"

        except Exception as e:
            log_event("ERROR", f"Couldn't use image from this vendor: {e}") 
        return None

    def download_image(self, url):
        r = requests.get(url, stream=True)
        r.raise_for_status()
        return BytesIO(r.content)

    def upload_to_wordpress(self, img_data, filename, caption):
        files = {
            "file": (filename, img_data, "image/jpeg")
        }
        data = {
            "caption": caption,
            "description": caption
        }

        r = requests.post(
            f"{self.wp_url}/wp-json/wp/v2/media",
            headers=self.wp_headers,
            files=files,
            data=data
        )
        r.raise_for_status()

        media_data = r.json()
        return {
            "id": media_data["id"],
            "url": media_data["source_url"]
        }
    
    def get_image_for_section(self, title, section):
        query = self.generate_keyword(title, section)
        for vendor in [
            self.search_unsplash,
            self.search_pexels,
            self.search_pixabay,
            self.search_wikimedia,
            self.search_freepik,
            ]:
            result = vendor(query)
            if result:
                img_url, attribution = result
                img_data = self.download_image(img_url)
                media_info = self.upload_to_wordpress(img_data, f"{query}.jpg", attribution)
                return media_info["id"], media_info["url"], attribution
        return None, None

bot = ImageIntegrationBot(
    wp_url=wordpress_url,
    wp_user=wordpress_username,
    wp_pass=wordpress_app_password,
    api_keys={
        "openai": openai_api_key,
        "pexels": pexels_api_key,
        "unsplash": unsplash_api_key,
        "pixabay": pixabay_api_key,
        "freepik": freepik_api_key
    }
)

