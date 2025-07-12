import os
from dotenv import load_dotenv

from openai_api import OpenAIClient
from ollama_api import generate_text
from wordpress_api import WordPressClient
from plagiarism_checker import PlagiarismChecker

# Load .env file
load_dotenv()

# Get environment variables
wordpress_url = os.getenv("WORDPRESS_URL")
wordpress_username = os.getenv("WORDPRESS_USERNAME")
wordpress_app_password = os.getenv("WORDPRESS_APP_PASSWORD")

openai_api_key = os.getenv("OPENAI_API_KEY")

ollama_url = os.getenv("OLLAMA_URL")
ollama_model = os.getenv("OLLAMA_MODEL")

plagiarism_api_key = os.getenv("PLAGIARISM_API_KEY")
plagiarism_api_url = os.getenv("PLAGIARISM_API_URL")


def main():

    # Setup clients
    # openai_client = OpenAIClient(openai_api_key)
    wp_client = WordPressClient(
        wordpress_url,
        wordpress_username,
        wordpress_app_password
    )
    plagiarism_checker = PlagiarismChecker()

    # Generate article
    print("📝 Generating content...")
    # article_content = openai_client.generate_text("Write a short blog post about AI in 2025")
    article_content = generate_text("Write a short blog post about AI in 2025. dont include ** in your headings e.g **3.", ollama_model)
    print("Article:", article_content)
    # Check plagiarism
    if plagiarism_checker.check(article_content):
        print("✅ Content passed plagiarism check")

        # Publish to WordPress
        post = wp_client.create_post("AI in 2025", article_content)
        print(f"Post published! ID: {post['id']}")
    else:
        print("Plagiarism detected. Post not published.")


if __name__ == "__main__":
    main()
