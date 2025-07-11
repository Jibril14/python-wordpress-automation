# bot/models.py
from dataclasses import dataclass
from typing import List


@dataclass
class Outline:
    title: str
    sections: List[str]


@dataclass
class Article:
    title: str
    excerpt: str
    content: str
    category: str
    tags: List[str]
