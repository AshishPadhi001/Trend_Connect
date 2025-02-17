##Follow_routes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from core.models import Follows, Registration
from core.database import get_db
from oauth2 import get_current_user
from schemas.follow import FollowRequest

router = APIRouter(
    tags=["Follow"]
)

@router.post("/follow",summary="Id you want to follow")
def follow_user(
    request: FollowRequest, 
    current_user: Registration = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """ Follow a user """
    if request.user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")

    if not db.query(Registration).filter_by(user_id=request.user_id).first():
        raise HTTPException(status_code=404, detail="User to follow not found")

    existing_follow = db.query(Follows).filter_by(follower_id=current_user.user_id, following_id=request.user_id).first()
    if existing_follow:
        raise HTTPException(status_code=400, detail="You are already following this user")

    follow_entry = Follows(follower_id=current_user.user_id, following_id=request.user_id, followed_at=datetime.utcnow())
    db.add(follow_entry)
    db.commit()
    return {"message": "Followed successfully"}

@router.delete("/unfollow",summary="Id you want to unfollow")
def unfollow_user(
    request: FollowRequest, 
    current_user: Registration = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """ Unfollow a user """
    follow_entry = db.query(Follows).filter_by(follower_id=current_user.user_id, following_id=request.user_id).first()
    if not follow_entry:
        raise HTTPException(status_code=400, detail="You are not following this user")

    db.delete(follow_entry)
    db.commit()
    return {"message": "Unfollowed successfully"}
