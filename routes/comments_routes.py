from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from core.database import get_db
from core import models
from oauth2 import get_current_user
from schemas.comments import CommentInput
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from configuration.config import settings  # Import settings from your config file
from tasks.comment_notify import notify_post_owner_background

router = APIRouter(
    tags=["Comments"]
)

# Manage comments on a post
@router.post("/comments", status_code=status.HTTP_201_CREATED, summary="Add a comment to a post")
def add_comment(
    comment: CommentInput,
    background_tasks: BackgroundTasks,  # Background task dependency
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Adds a comment to a post and notifies the post owner in the background.
    """
    # Check if the post exists
    post = db.query(models.Content).filter(models.Content.c_id == comment.post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    # Create a new comment entry in the database
    new_comment = models.Comment(
        user_id=current_user.user_id,  
        post_id=comment.post_id,
        user_comment=comment.user_comment
    )

    # Add and commit the new comment to the database
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    # Notify the post owner in the background
    background_tasks.add_task(notify_post_owner_background, comment.post_id, comment.user_comment, current_user.username, db, background_tasks)

    return {
        "message": "Comment added successfully",
        "comment": {
            "user_id": new_comment.user_id,
            "post_id": new_comment.post_id,
            "user_comment": new_comment.user_comment,
            "comment_id": new_comment.comment_id,  
        }
    }
