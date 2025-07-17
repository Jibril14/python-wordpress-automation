# bot/models.py
from dataclasses import dataclass
from typing import List

from dataclasses import dataclass

@dataclass
class Article:
    title: str
    content: str
    tags: list = None
    categories: list = None

# tags: List[str]
