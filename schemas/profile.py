from pydantic import BaseModel
from typing import List

# Assuming ContentDetailResponse is already defined somewhere else
class ContentDetailResponse(BaseModel):
    username: str
    title: str
    caption: str
    created_at: str
    comments: List[str]
    total_likes: int

class UserProfileResponse(BaseModel):
    username: str
    followers: int  # Added followers count
    following: int  # Added following count
    content: List[ContentDetailResponse]
