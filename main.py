import os
from dotenv import load_dotenv

from models.article import Article
from utils.text_cleaner import clean_article_text
from utils.file_handler import save_draft
from core.logger import log_event
from core.ollama_api import generate_text
from core.wordpress_api import WordPressClient
from core.plagiarism_checker import PlagiarismChecker

load_dotenv()

wordpress_url = os.getenv("WORDPRESS_URL")
wordpress_username = os.getenv("WORDPRESS_USERNAME")
wordpress_app_password = os.getenv("WORDPRESS_APP_PASSWORD")
ollama_model = os.getenv("OLLAMA_MODEL")

def main():
    # Setup clients
    wp_client = WordPressClient(
        wordpress_url,
        wordpress_username,
        wordpress_app_password
    )
    plagiarism_checker = PlagiarismChecker()

    # Generate article
    log_event("INFO", "Starting article generation")
    prompt = "Write a short blog post about AI in 2025. Don't include ** in headings."
    raw_content = generate_text(prompt, ollama_model)

    # Clean and structure article
    cleaned_content = clean_article_text(raw_content)
    article = Article(title="AI in 2025", content=cleaned_content)

    # Save draft locally
    draft_path = save_draft(article.title, article.content)
    log_event("INFO", "Draft saved", {"path": str(draft_path)})

    # Check plagiarism
    log_event("INFO", "Running plagiarism check")
    if plagiarism_checker.check(article.content):
        log_event("SUCCESS", "Content passed plagiarism check")
        post = wp_client.create_post(article.title, article.content)
        log_event("SUCCESS", "Post published", {"post_id": post.get("id")})
        print(f"Post published! ID: {post['id']}")
    else:
        log_event("WARNING", "Plagiarism detected. Post not published.")
        print("Plagiarism detected. Post not published.")

if __name__ == "__main__":
    main()
