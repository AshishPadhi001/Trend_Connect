#Comments.py
from pydantic import BaseModel

class CommentInput(BaseModel):
    post_id: int
    user_comment: str
