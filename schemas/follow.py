from pydantic import BaseModel

class FollowRequest(BaseModel):
    user_id: int  # The ID of the user to follow/unfollow

    class Config:
        from_attribute = True
