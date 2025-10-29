from pydantic import BaseModel
from typing import List, Optional

class Article(BaseModel):
    url: str
    title: str
    content: Optional[str] = None
    published_date: Optional[str] = None
    summary: Optional[str] = None

class ArticleList(BaseModel):
    articles: List[Article]

class FinalReport(BaseModel):
    editorial: str
    articles: List[Article]
    approved: bool = False
    feedback: str = ""
    topic_name: str

class Editorial(BaseModel):
    main_title: str
    editorial_content: str
    final_report: List[FinalReport]

class Newsletter(BaseModel):
    html_content: str
