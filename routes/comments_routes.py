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
from Logging.logging import logger
import time

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
    start_time = time.time()
    logger.info(f"Comment addition attempt by user {current_user.username} on post {comment.post_id}")
    
    try:
        # Check if the post exists
        post = db.query(models.Content).filter(models.Content.c_id == comment.post_id).first()
        if not post:
            logger.warning(f"Comment failed: Post with ID {comment.post_id} not found")
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

        # Log the successful comment creation
        logger.info(f"Comment {new_comment.comment_id} added successfully by user {current_user.username} on post {comment.post_id}")
        
        # Notify the post owner in the background
        background_tasks.add_task(notify_post_owner_background, comment.post_id, comment.user_comment, current_user.username, db, background_tasks)
        logger.info(f"Background notification task scheduled for post owner of post {comment.post_id}")

        execution_time = time.time() - start_time
        logger.info(f"Comment operation completed in {round(execution_time * 1000, 2)} ms")
        
        return {
            "message": "Comment added successfully",
            "comment": {
                "user_id": new_comment.user_id,
                "post_id": new_comment.post_id,
                "user_comment": new_comment.user_comment,
                "comment_id": new_comment.comment_id,  
            }
        }
    except HTTPException:
        # Re-raise HTTP exceptions after logging
        raise
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error in add_comment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while adding comment"
        )