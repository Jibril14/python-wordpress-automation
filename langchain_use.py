from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel
import pandas as pd
from typing import List
import json


# from langchain.llms import Ollama  
# llm = Ollama(model="llama3.2:latest") 

from langchain_ollama import OllamaLLM # Works with my local Ollama

llm = OllamaLLM(
    model="llama3.2:latest",
    base_url="http://localhost:11434"  # explicitly set your Ollama server URL
)


# ====== Structured output models ======

class Section(BaseModel):
    heading: str
    content: str

class ArticleOutline(BaseModel):
    sections: List[Section]

outline_parser = PydanticOutputParser(pydantic_object=ArticleOutline)
# print("outline_parser.get_format_instructions()", outline_parser.get_format_instructions())

# ====== Template generator ======

def build_outline_prompt(main_keyword, reference_links, secondary_keywords):
    """Mimics your Go template branching logic."""
    ref_links_str = ", ".join(reference_links) if reference_links else ""
    secondary_str = ", ".join(secondary_keywords) if secondary_keywords else ""

    if not reference_links and not secondary_keywords:
        base_prompt = (
            f"I want you to be an expert in Food and Recipes and Generate an article outline for the topic \"{main_keyword}\"."
        )
    elif reference_links and not secondary_keywords:
        base_prompt = (
            f"I want you to be an expert in food and culinary writing and Generate an article outline for the topic \"{main_keyword}\" "
            f"and use the following articles as the primary source of reference: \"{ref_links_str}\""
        )
    elif reference_links and secondary_keywords:
        base_prompt = (
            f"I want you to be an expert in food and culinary writing and Generate an article outline for the topic \"{main_keyword}\" "
            f"and use the following articles as the primary source of reference: \"{ref_links_str}\". "
            f"Make sure to discuss these in the article: \"{secondary_str}\""
        )
    elif secondary_keywords and not reference_links:
        base_prompt = (
            f"I want you to be an expert in food and culinary writing and Generate an article outline for the topic \"{main_keyword}\", "
            f"while making sure to discuss these in the article: \"{secondary_str}\""
        )

    # Append the JSON structure instructions
    base_prompt += (
        "\nGive me strictly just the outline as output, there should be Introduction heading at the start followed by the individual "
        "headings for the content. No need for Conclusion. Use H2 style headings for each entry, and there should be no subheadings. "
        "Make the headings engaging, but keep it under 50 characters. Do not give me any additional text other than the outline.\n"
        f"Here is the format:\n{outline_parser.get_format_instructions()}"
    )

    print("Base Prompt:", base_prompt)
    return base_prompt

# ====== Content template (for_content.tmpl) ======

def build_content_prompt(main_keyword, sections):
    """Replicates your for_content.tmpl logic."""
    section_titles = "\n".join(s.heading for s in sections)
    return (
        "Write as a culinary expert with a strong command of food preparation, presenting each recipe in a clear, inviting, and grounded tone. "
        "Focus on useful techniques, ingredient highlights, and small details that help readers improve their results in the kitchen. "
        "Avoid overly casual language or imaginative openers like “Imagine” or “Picture this.” Instead, begin each section with a direct yet "
        "natural sentence that introduces the idea or dish without unnecessary flair.\n\n"
        "Use vivid but practical language that brings attention to textures, flavors, and cooking methods. Prioritize clarity, helpfulness, "
        "and appeal to home cooks looking for reliable inspiration. Every section—including the introduction—should be between 450–600 characters "
        "and maintain a steady rhythm, avoiding repetitive phrases or storytelling tropes.\n\n"
        "Your goal is to make the content feel fresh, knowledgeable, and actionable—something a food-savvy reader would want to try immediately, "
        "without wading through fluff.\n\n"
        f"Only return the content for the following sections without adding any extra commentary or explanations:\n{section_titles}\n\n"
        f"Make sure the content generated is in reference to the title at hand: \"{main_keyword}\""
    )

# ====== Main pipeline ======

def run_pipeline(csv_path, llm):
    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        main_keyword = row["Main Keyword"]
        reference_links = row["Reference Links"].split(",") if pd.notna(row["Reference Links"]) else []
        secondary_keywords = row["Secondary Keywords"].split(",") if pd.notna(row["Secondary Keywords"]) else []

        # Step 1: Build outline prompt
        outline_prompt = build_outline_prompt(main_keyword, reference_links, secondary_keywords)
        print("Outline_prompt:", outline_prompt)
        # # Call LLM for outline
        outline_response = llm.invoke(outline_prompt)
        outline = outline_parser.parse(outline_response)
        print("_outline Parser:", outline)

        # # Step 2: Build content prompt
        # content_prompt = build_content_prompt(main_keyword, outline.sections)
        # content_response = llm.invoke(content_prompt)

        # print(f"=== {main_keyword} ===")
        # print(content_response)

run_pipeline("./data.csv", llm)

