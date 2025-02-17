##Content.py

from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

# Content creation request model
class ContentCreate(BaseModel):
    title: str
    caption: str
    username: str

# Response model for when content is created or fetched (summary)
class ContentResponse(BaseModel):
    c_id: int
    username: str
    title: str
    caption: str
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic will treat SQLAlchemy models as dictionaries

# Model for updating existing content
class ContentUpdate(BaseModel):
    title: Optional[str] = None
    caption: Optional[str] = None

# Detailed response model for content with additional information
class ContentDetailResponse(BaseModel):
    username: str
    title: str
    caption: str
    created_at: datetime
    file: Optional[str] = None  # File associated with content, if any
    comments: List[str] = []  # List of comments on the content
    total_likes: int = 0  # Total number of likes

    class Config:
        from_attributes = True  # Ensure SQLAlchemy models work with Pydantic using from_attributes
