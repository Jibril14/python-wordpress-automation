import re

def clean_article_text(text: str) -> str:
    """
    Remove extra spaces, fix headings, and strip unwanted characters.
    """
    text = re.sub(r"\n{3,}", "\n\n", text)  # No triple newlines
    text = text.strip()
    return text
