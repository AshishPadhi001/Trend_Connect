from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from core.database import get_db
from core import models
from oauth2 import get_current_user
from schemas.likes import LikeInput  # Ensure this schema includes post_id and dir
from tasks.notify_user import notify_post_owner_background  # Import the background task function

router = APIRouter(
    tags=["Likes"]
)

# Manage likes on a post
@router.post("/likes", status_code=status.HTTP_201_CREATED, summary="Like or unlike a post")
def manage_likes(
    background_tasks: BackgroundTasks,  # Directly pass BackgroundTasks here
    like: LikeInput, 
    db: Session = Depends(get_db), 
    current_user: str = Depends(get_current_user),
):
    """
    Likes or unlikes a post based on the direction (1 for like, 0 for unlike).
    After liking, it sends an email notification to the post owner.
    """
    # Check if the post exists
    post = db.query(models.Content).filter(models.Content.c_id == like.post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No post found")

    # Check if the user has already liked the post
    found_like = db.query(models.Likes).filter(
        models.Likes.user_id == current_user.user_id,
        models.Likes.post_id == like.post_id
    ).first()

    if like.dir == 1:  # Like the post
        if found_like:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Post already liked")

        # Add the like to the post
        new_like = models.Likes(user_id=current_user.user_id, post_id=like.post_id)
        db.add(new_like)
        db.commit()

        # Fetch the current user's username (from current_user)
        username = current_user.username  # Assuming 'current_user' has a 'username' attribute

        # Notify the post owner about the like in the background
        background_tasks.add_task(notify_post_owner_background, like.post_id, db, username)

        return {"message": "Post liked successfully"}

    else:  # Unlike the post
        if not found_like:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No like found")

        db.delete(found_like)
        db.commit()

        return {"message": "Post unliked successfully"}
