##Likes.py

from pydantic import BaseModel, Field

class LikeInput(BaseModel):
    post_id: int
    dir: int = Field(ge=0, le=1)
