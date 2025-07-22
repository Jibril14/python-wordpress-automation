import os
import requests
import json
from io import BytesIO
from base64 import b64encode
from openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from templates.article_outline import STRING_SIX

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
        self.wp_headers = {'Authorization': f'Basic {token.decode("utf-8")}'}
        self.api_keys = api_keys
        # self.oa_client = OpenAI(api_key=api_keys['openai'])

    # def generate_keyword(self, title, section):
    #     prompt = f"""
    #     Blog Title: {title}
    #     Section: {section}
    #     Task: Return a short keyword phrase (2-5 words) describing an image for this section.
    #     """
    #     resp = self.oa_client.chat.completions.create(
    #         model="gpt-4o-mini",
    #         messages=[{"role": "user", "content": prompt}]
    #     )
    #     return resp.choices[0].message.content.strip()


    def generate_keyword(self, title, section):
        # Create the LLM instance
        llm = ChatOpenAI(
            model=openai_model,
            temperature=0.7,
            api_key=openai_api_key
        )

        # Create the prompt
        prompt_template = PromptTemplate.from_template("{prompt}")

        # Chain the prompt into the model
        chain = prompt_template | llm

        # Build the full prompt
        full_prompt = f"""
        Blog Title: {title}
        Section: {section}

        {STRING_SIX}
        """
        print("full_prompt:", full_prompt)
        try:
            result = chain.invoke({"prompt": full_prompt})
            print("KEYWORD:", result.content)
            return result.content.strip()
        except Exception as e:
            print("OpenAI keyword generation error:", e)
            return None


    def search_pexels(self, query):
        try:
            url = f"https://api.pexels.com/v1/search?query={query}"
            r = requests.get(url, headers={"Authorization": self.api_keys['pexels']})
            r.raise_for_status()
            data = r.json()
            if data['photos']:
                img = data['photos'][0]
                print("Pixel Image:", data['photos'][0])
                return img['src']['large'], f"Photo by {img['photographer']} on Pexels"
        except Exception as e:
            print("Pexels error:", e)
        return None

    def search_unsplash(self, query):
        try:
            url = f"https://api.unsplash.com/search/photos?query={query}&client_id={self.api_keys['unsplash']}"
            r = requests.get(url)
            r.raise_for_status()
            data = r.json()
            if data['results']:
                img = data['results'][0]
                print("Unsplash Image:", img['urls']['regular'])
                return img['urls']['regular'], f"Photo by {img['user']['name']} on Unsplash"
        except Exception as e:
            print("Unsplash error:", e)
        return None

    def search_pixabay(self, query):
        try:
            url = f"https://pixabay.com/api/?key={self.api_keys['pixabay']}&q={query}"
            r = requests.get(url)
            r.raise_for_status()
            data = r.json()
            if data['hits']:
                img = data['hits'][0]
                print("Pixabay IMG:", img['largeImageURL'])
                return img['largeImageURL'], f"Image by {img['user']} from Pixabay"
        except Exception as e:
            print("Pixabay error:", e)
        return None
    
    def search_freepik(self, query):
        try:
            headers = {
                "x-freepik-api-key": self.api_keys['freepik']
            }

            # Step 1: Search for resources
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

            # Step 2: Loop through results and pick first direct image
            for item in data["data"]:
                resource_id = item["id"]
                title = item.get("title", "Freepik image")
                author_name = item.get("author", {}).get("name", "")

                # Step 3: Get download URL
                download_url = f"https://api.freepik.com/v1/resources/{resource_id}/download"
                dl = requests.get(download_url, headers=headers)
                dl.raise_for_status()
                dl_data = dl.json()
                img_url = dl_data["data"]["url"]

                # Step 4: Filter only jpg/png
                if img_url.lower().endswith((".jpg", ".jpeg", ".png")):
                    attribution = f"{title} by {author_name} on Freepik"
                    return img_url, attribution

            # If we got here, no valid JPG/PNG found
            return None

        except Exception as e:
            print("Freepik error:", e)
            return None


    def search_wikimedia(self, query):
        try:
            headers = {
                "User-Agent": "WPImageBot/1.0 (https://foodnservice.com/contact)"
            }

            # Step 1: Search for file pages only
            search_url = "https://commons.wikimedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": query,
                "srnamespace": 6,  # Only File namespace
                "srlimit": 5       # Get a few to filter later
            }
            r = requests.get(search_url, params=params, headers=headers)
            r.raise_for_status()
            data = r.json()

            if not data['query']['search']:
                return None

            # Step 2: Loop through results to find first actual image
            for result in data['query']['search']:
                file_title = result['title']  # e.g., 'File:Example.jpg'

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
                print("Image_data", image_data)

                pages = image_data["query"]["pages"]
                for page in pages.values():
                    if "imageinfo" in page:
                        info = page["imageinfo"][0]
                        mime = info.get("mime", "")
                        if mime.startswith("image/"):  # Only accept images
                            img_url = info["url"]
                            print("WIKI IMG:*********", img_url)
                            return img_url, f"Image from Wikimedia Commons ({file_title})"

        except Exception as e:
            print("Wikimedia error:", e)

        return None

    def download_image(self, url):
        r = requests.get(url, stream=True)
        r.raise_for_status()
        return BytesIO(r.content)

    def upload_to_wordpress(self, img_data, filename, caption):
        files = {'file': (filename, img_data)}
        data = {'caption': caption, 'description': caption}
        r = requests.post(f"{self.wp_url}/wp-json/wp/v2/media",
                          headers=self.wp_headers,
                          files=files,
                          data=data)
        r.raise_for_status()
        return json.loads(r.content)['source_url']

    def get_image_for_section(self, title, section):
        query = self.generate_keyword(title, section)
        for vendor in [self.search_pexels, self.search_unsplash, self.search_pixabay, self.search_wikimedia, self.search_freepik]:
            result = vendor(query)
            if result:
                img_url, attribution = result
                img_data = self.download_image(img_url)
                wp_img_url = self.upload_to_wordpress(img_data, f"{query}.jpg", attribution)
                print("wp_img_url:", wp_img_url)

                return wp_img_url, attribution
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

title = "People in love"
section = """
Boy and girls kissing
"""
img_url, attribution = bot.get_image_for_section(title, section)
print(img_url, attribution)
