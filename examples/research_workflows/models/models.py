from pydantic import BaseModel, Field
from typing import List


class Article(BaseModel):
    topic: str
    title: str
    summary: str
    url: str
    published_date: str


class NewsletterPayload(BaseModel):
    main_editorial: str
    articles: List[Article]


class PromptOptimizationResult(BaseModel):
    optimized_prompt: str = Field(
        ..., 
        description="The optimized instruction for the ReActAgent"
    )
    feedback: str = Field(
        ..., 
        description="Explanation of improvements made"
    )
    iteration_count: int = Field(
        default=0,
        description="Number of optimization iterations performed"
    )
    quality_scores: dict = Field(
        default_factory=dict,
        description="Final quality scores from critique"
    )