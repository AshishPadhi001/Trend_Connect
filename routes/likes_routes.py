from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from core.database import get_db
from core import models
from oauth2 import get_current_user
from schemas.likes import LikeInput
from tasks.notify_user import notify_post_owner_background
from Logging.logging import logger
import time

router = APIRouter(
    tags=["Likes"]
)

@router.post("/likes", status_code=status.HTTP_201_CREATED, summary="Like or unlike a post")
def manage_likes(
    background_tasks: BackgroundTasks,
    like: LikeInput, 
    db: Session = Depends(get_db), 
    current_user: str = Depends(get_current_user),
):
    """
    Likes or unlikes a post based on the direction (1 for like, 0 for unlike).
    After liking, it sends an email notification to the post owner.
    """
    start_time = time.time()
    action = "like" if like.dir == 1 else "unlike"
    logger.info(f"{action.capitalize()} request from user {current_user.username} for post {like.post_id}")

    try:
        # Check if the post exists
        post = db.query(models.Content).filter(models.Content.c_id == like.post_id).first()
        if not post:
            logger.warning(f"Like action failed: Post {like.post_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No post found")

        # Check if the user has already liked the post
        found_like = db.query(models.Likes).filter(
            models.Likes.user_id == current_user.user_id,
            models.Likes.post_id == like.post_id
        ).first()

        if like.dir == 1:  # Like the post
            if found_like:
                logger.warning(f"Like action failed: User {current_user.username} has already liked post {like.post_id}")
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Post already liked")

            # Add the like to the post
            new_like = models.Likes(user_id=current_user.user_id, post_id=like.post_id)
            db.add(new_like)
            db.commit()
            logger.info(f"Like created: User {current_user.username} liked post {like.post_id}")

            # Get total likes for the post
            total_likes = db.query(models.Likes).filter(models.Likes.post_id == like.post_id).count()
            logger.info(f"Post {like.post_id} now has {total_likes} likes")

            # Schedule notification
            username = current_user.username
            background_tasks.add_task(notify_post_owner_background, like.post_id, db, username)
            logger.info(f"Background notification task scheduled for post owner about like from {username}")

            execution_time = time.time() - start_time
            logger.info(f"Like operation completed in {round(execution_time * 1000, 2)} ms")
            
            return {"message": "Post liked successfully"}

        else:  # Unlike the post
            if not found_like:
                logger.warning(f"Unlike action failed: No like found for user {current_user.username} on post {like.post_id}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No like found")

            db.delete(found_like)
            db.commit()
            logger.info(f"Like removed: User {current_user.username} unliked post {like.post_id}")

            # Get updated total likes
            total_likes = db.query(models.Likes).filter(models.Likes.post_id == like.post_id).count()
            logger.info(f"Post {like.post_id} now has {total_likes} likes")

            execution_time = time.time() - start_time
            logger.info(f"Unlike operation completed in {round(execution_time * 1000, 2)} ms")
            
            return {"message": "Post unliked successfully"}

    except HTTPException as he:
        # Log the HTTP exception but re-raise it
        execution_time = time.time() - start_time
        logger.warning(f"HTTP Exception in {action} operation after {round(execution_time * 1000, 2)} ms: {str(he.detail)}")
        raise he
    except Exception as e:
        # Log unexpected errors
        execution_time = time.time() - start_time
        logger.error(f"Unexpected error in {action} operation after {round(execution_time * 1000, 2)} ms: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error occurred while processing {action} request: {str(e)}"
        )