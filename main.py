import os
import json
from typing import Any, Dict
import jsonschema
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path
from retrying import retry
from models.article import Article
from utils.text_cleaner import clean_article_text
from utils.file_handler import save_draft
from core.logger import log_event
from core.wordpress_api import WordPressClient
from core.plagiarism_checker import PlagiarismChecker

from langchain.prompts import PromptTemplate
from langchain.schema import OutputParserException
from langchain_openai import ChatOpenAI


load_dotenv()

wordpress_url = os.getenv("WORDPRESS_URL")
wordpress_username = os.getenv("WORDPRESS_USERNAME")
wordpress_app_password = os.getenv("WORDPRESS_APP_PASSWORD")
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_model = os.getenv("OPENAI_MODEL")
ollama_model = os.getenv("OLLAMA_MODEL")



def build_article_outline_prompt(main_keyword, reference_links=None, secondary_keywords=None):
    reference_links = reference_links or []
    secondary_keywords = secondary_keywords or []

    if not reference_links and not secondary_keywords:
        intro = f'I want you to be an expert in Food and Recipes and Generate an article outline for the topic "{main_keyword}".'
    elif reference_links and not secondary_keywords:
        intro = (
            f'I want you to be an expert in food and culinary writing and Generate an article outline for the topic "{main_keyword}" '
            f'and use the following articles as the primary source of reference: "{", ".join(reference_links)}"'
        )
    elif reference_links and secondary_keywords:
        intro = (
            f'I want you to be an expert in food and culinary writing and Generate an article outline for the topic "{main_keyword}" '
            f'and use the following articles as the primary source of reference: "{", ".join(reference_links)}". '
            f'Make sure to discuss these in the article: "{", ".join(secondary_keywords)}"'
        )
    elif secondary_keywords and not reference_links:
        intro = (
            f'I want you to be an expert in food and culinary writing and Generate an article outline for the topic "{main_keyword}", '
            f'while making sure to discuss these in the article: "{", ".join(secondary_keywords)}"'
        )

    final_instruction = (
        "Give me strictly just the outline as output, there should be Introduction heading at the start followed by the individual headings for the content. "
        "No need for Conclusion. Use H2 style headings for each entry, and there should be no subheadings. "
        "Make the headings engaging, but keep it under 50 characters. Do not give me any additional text other than the outline. "
        "Make sure the output is in JSON so that it's easier to access the headings.\n"
        'Here\'s the JSON structure I want to use.'
    )

    return f"{intro}\n\n{final_instruction}"


# ----- Helpers -----
def load_prompt(template_name: str, **kwargs) -> str:
    path = Path("templates") / f"{template_name}.txt"
    template = path.read_text(encoding="utf-8")
    return template.format(**kwargs)

def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load the JSON schema file containing both example and schema."""
    path = Path("schemas") / f"{schema_name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_name}")
    return json.loads(path.read_text(encoding="utf-8"))

def run_llm(template_name: str, schema_name: str, **kwargs):
    """Run a template + schema (example embedded) with manual JSON parsing."""
    
    # Load schema + example from file
    schema_file = load_schema(schema_name)
    example_json = schema_file["example"]
    json_schema = schema_file["format"]

    format_instructions = f"""
    Here is an example of correct output:
    {json.dumps(example_json, indent=4)}

    These examples are just to guide you donot include them in the final output
    """

    prompt_text = load_prompt(template_name, **kwargs)
    # full_prompt = prompt_text.replace("{{format_instructions}}", format_instructions)
    full_prompt = f"""{prompt_text}
    {format_instructions}
    """

    print("\n")
    print("Full Prompt Sent to run_llm:\n", full_prompt)

    llm = ChatOpenAI(
        model=openai_model,
        temperature=0.7,
        api_key=openai_api_key,
        response_format = json_schema
    )

    chain = PromptTemplate.from_template("{prompt}") | llm

    result = chain.invoke({"prompt": full_prompt})
    print("OpenAI (result.content) 1:", result.content)

    try:     
        return json.loads(result.content)
    except Exception as err:
        log_event("ERROR", f"{schema_name}: {err}")  
        return None     

def run_llm_from_text(prompt_text: str, schema_name: str):
    """Run plain text prompt using example-based formatting and schema validation."""
    schema_file = load_schema(schema_name)
    json_example = schema_file["example"]
    json_schema = schema_file["format"]

    format_instructions = f"""
    Respond ONLY in valid JSON that strictly matches this format.
    All keys and strings must be enclosed in double quotes.
    You MUST include every field exactly as in the example.

    {json.dumps(json_example, indent=4)}

    """

    full_prompt = f"""{prompt_text}

    {format_instructions}
    """
    print("Full Prompt:", full_prompt)


    llm = ChatOpenAI(
        model=openai_model,
        temperature=0.7,
        api_key=openai_api_key,
        response_format = json_schema
    )

    chain = PromptTemplate.from_template("{prompt}") | llm
    try:
        result = chain.invoke({"prompt": full_prompt})
        print("OpenAI (result.content) 2:", result.content)
        return json.loads(result.content)
    except Exception as err:
        print("===Failed Perse and Validated LLM Output 1===")
        log_event("ERROR", f"JSON does not match schema: {err}")
        return None 

def process_row(main_keyword, reference_links, secondary_keywords):
    log_event("INFO", f"Processing keyword: {main_keyword}")
    
    outline_prompt = build_article_outline_prompt(main_keyword, reference_links, secondary_keywords)
    outline = run_llm_from_text(outline_prompt, schema_name="outline_structoutput")
    print("Prompt Schema Outline Gen********:", outline)

    try:
        if not outline:
            log_event("ERROR", f"Article outline generation failed on  attempt")
    except Exception as err:
        log_event("ERROR", f"Article outline generation failed: {err}")
        log_event("WARNING", f"Continuing despite error: {err}")

    # Build Chunks from outline (assuming JSON structure like: {"sections": [{"heading": "..."}]})
    chunks_text = ""
    if isinstance(outline, dict):
        sections = outline.get("sections") or outline.get("headings") or []
        print("Section***********", sections)
        if isinstance(sections, list):
            chunks_text = "\n".join(
                sec.get("heading", "").strip()
                if isinstance(sec, dict) else str(sec).strip()
                for sec in sections
            )

    content = run_llm(
        template_name="for_content",
        schema_name="content_structoutput",
        MainKeyword=main_keyword,
        Outline=json.dumps(outline, ensure_ascii=False),
        Chunks=chunks_text
    )
    excerpt = run_llm(
        template_name="for_excerpt",
        schema_name="excerpt_structoutput",
        MainKeyword=main_keyword
    )
    return content, excerpt

def main():
    wp_client = WordPressClient(
        wordpress_url,
        wordpress_username,
        wordpress_app_password
    )
    plagiarism_checker = PlagiarismChecker()

    df = pd.read_csv("data.csv")

    for _, row in df.iterrows():
        main_keyword = row.get("Main Keyword", "").strip()
        reference_links = row.get("Reference Links", "").split(",")
        secondary_keywords = row.get("Secondary Keywords", "").split(",")
        print("Main keyword *******:", main_keyword)
        print("Reference Links *******:", reference_links)
        print("Secondary Keywords *******:", secondary_keywords)
        content, excerpt = process_row(main_keyword, reference_links, secondary_keywords)
        print("***************CONTENT************", content)
        print("***************Excerpt************", excerpt)

        if not content and excerpt:
            log_event("ERROR", "Content generation failed")
        else:
            full_article = ""
            for section in content["sections"]:
                cleaned_heading = clean_article_text(section["heading"])
                cleaned_content = clean_article_text(section["content"])

                each_section = cleaned_heading + "\n\n" + cleaned_content # Later I'll add image
                full_article += each_section + "\n\n"
            print("FULL*******Article", full_article)
            article = Article(title=main_keyword, content=full_article, excerpt=excerpt.get("excerpt", ""))

            draft_path = save_draft(article.title, article.content)
            log_event("INFO", "Draft saved", {"path": str(draft_path)})

            log_event("INFO", "Running plagiarism check")
            if plagiarism_checker.check(article.content):
                log_event("SUCCESS", "Content passed plagiarism check")
                post = wp_client.create_post(article.title, article.content, excerpt=article.excerpt)
                log_event("SUCCESS", "Post published", {"post_title": post.get("title")})
                print(f"Post published! ID: {post['id']}")
            else:
                log_event("WARNING", "Plagiarism detected. Post not published.")
                print("Plagiarism detected. Post not published.")

if __name__ == "__main__":
    main()
