from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from core.models import Follows, Registration
from core.database import get_db
from oauth2 import get_current_user
from schemas.follow import FollowRequest
from Logging.logging import logger
import time

router = APIRouter(
    tags=["Follow"]
)

@router.post("/follow", summary="Id you want to follow")
def follow_user(
    request: FollowRequest, 
    current_user: Registration = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Follow a user"""
    start_time = time.time()
    logger.info(f"Follow request from user {current_user.user_id} to follow user {request.user_id}")

    try:
        # Check if user is trying to follow themselves
        if request.user_id == current_user.user_id:
            logger.warning(f"User {current_user.user_id} attempted to follow themselves")
            raise HTTPException(status_code=400, detail="You cannot follow yourself")

        # Check if target user exists
        target_user = db.query(Registration).filter_by(user_id=request.user_id).first()
        if not target_user:
            logger.warning(f"Follow attempt failed: Target user {request.user_id} not found")
            raise HTTPException(status_code=404, detail="User to follow not found")

        # Check if already following
        existing_follow = db.query(Follows).filter_by(
            follower_id=current_user.user_id, 
            following_id=request.user_id
        ).first()
        
        if existing_follow:
            logger.warning(f"User {current_user.user_id} already follows user {request.user_id}")
            raise HTTPException(status_code=400, detail="You are already following this user")

        # Create new follow relationship
        follow_entry = Follows(
            follower_id=current_user.user_id,
            following_id=request.user_id,
            followed_at=datetime.utcnow()
        )
        db.add(follow_entry)
        db.commit()
        
        execution_time = time.time() - start_time
        logger.info(f"Follow relationship created: User {current_user.user_id} now follows {request.user_id}. Completed in {round(execution_time * 1000, 2)} ms")
        
        return {"message": "Followed successfully"}

    except HTTPException as he:
        # Re-raise HTTP exceptions as they're already handled
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in follow_user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error occurred while following user: {str(e)}")

@router.delete("/unfollow", summary="Id you want to unfollow")
def unfollow_user(
    request: FollowRequest,
    current_user: Registration = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unfollow a user"""
    start_time = time.time()
    logger.info(f"Unfollow request from user {current_user.user_id} to unfollow user {request.user_id}")

    try:
        # Check if follow relationship exists
        follow_entry = db.query(Follows).filter_by(
            follower_id=current_user.user_id,
            following_id=request.user_id
        ).first()

        if not follow_entry:
            logger.warning(f"Unfollow failed: User {current_user.user_id} is not following user {request.user_id}")
            raise HTTPException(status_code=400, detail="You are not following this user")

        # Remove follow relationship
        db.delete(follow_entry)
        db.commit()

        execution_time = time.time() - start_time
        logger.info(f"Follow relationship removed: User {current_user.user_id} unfollowed {request.user_id}. Completed in {round(execution_time * 1000, 2)} ms")

        return {"message": "Unfollowed successfully"}

    except HTTPException as he:
        # Re-raise HTTP exceptions as they're already handled
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in unfollow_user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error occurred while unfollowing user: {str(e)}")