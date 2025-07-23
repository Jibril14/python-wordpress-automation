import re

def clean_article_text(text: str) -> str:
    """
    Remove extra spaces, em character, fix headings, and strip unwanted characters.
    """
    text = text.replace("—", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    return text
