from pydantic import BaseModel
from typing import List, Optional

class Headline(BaseModel):
    topic: str
    images: List[str]
    categories: List[str]
    isLatest: bool
    url: str
    route: str

class ArticleDetail(BaseModel):
    topic: str
    images: List[str]
    categories: List[str]
    descriptions: List[str]
    url: str

class LiveTV(BaseModel):
    video_url: str
    title: str

class StatusEvent(BaseModel):
    status: str  # loading, fetching, syncing, ready, error
    message: Optional[str] = None
    timestamp: str
