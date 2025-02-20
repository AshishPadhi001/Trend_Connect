from fastapi import FastAPI, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from core.models import Registration, Content, Likes, Comment, Follows
from schemas.profile import UserProfileResponse, ContentDetailResponse
from core.database import get_db
from utils.hashing import verify
from Logging.logging import logger
import time

router = APIRouter(
    tags=['Profile']
)

@router.post("/user_profile", response_model=UserProfileResponse, summary="Login of registered user")
def profile_login(
    user_credential: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate the user using username and password, then return the user's profile, content,
    followers count, and following count.
    """
    start_time = time.time()
    logger.info(f"Profile login attempt for user: {user_credential.username}")

    try:
        # Query the user by username
        user = db.query(Registration).filter(Registration.username == user_credential.username).first()

        if not user:
            logger.warning(f"Login failed: User not found - {user_credential.username}")
            raise HTTPException(status_code=404, detail="User not found")

        # Validate the password
        if not verify(user_credential.password, user.password):
            logger.warning(f"Login failed: Incorrect password for user {user_credential.username}")
            raise HTTPException(status_code=401, detail="Incorrect password")

        logger.info(f"Password verification successful for user {user_credential.username}")

        # Count followers and following
        followers_count = db.query(Follows).filter(Follows.following_id == user.user_id).count()
        following_count = db.query(Follows).filter(Follows.follower_id == user.user_id).count()
        logger.info(f"User {user_credential.username} has {followers_count} followers and is following {following_count} users")

        # Prepare user profile response
        user_profile = {
            "username": user.username,
            "followers": followers_count,
            "following": following_count,
            "content": []
        }

        # Fetch the user's content
        content_list = db.query(Content).filter(Content.username == user.username).all()
        logger.info(f"Retrieved {len(content_list)} content items for user {user_credential.username}")

        for c in content_list:
            likes_count = db.query(Likes).filter(Likes.post_id == c.c_id).count()
            comments = db.query(Comment).filter(Comment.post_id == c.c_id).all()
            comment_texts = [comment.user_comment for comment in comments]

            content_details = ContentDetailResponse(
                username=c.username,
                title=c.title,
                caption=c.caption,
                created_at=c.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                comments=comment_texts,
                total_likes=likes_count
            )
            user_profile["content"].append(content_details)

        execution_time = time.time() - start_time
        logger.info(f"Profile login completed for user {user_credential.username} in {round(execution_time * 1000, 2)} ms")
        
        return user_profile

    except HTTPException as he:
        execution_time = time.time() - start_time
        logger.warning(f"HTTP Exception in profile login after {round(execution_time * 1000, 2)} ms: {str(he.detail)}")
        raise he
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Unexpected error in profile login after {round(execution_time * 1000, 2)} ms: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error occurred during profile login: {str(e)}")

@router.get("/followers/{username}", summary="Get the users who follow a specific user")
def get_followers(
    username: str,
    db: Session = Depends(get_db)
):
    """
    Get the list of users who follow the specified user, with details including the date they followed.
    """
    start_time = time.time()
    logger.info(f"Fetching followers for user: {username}")

    try:
        # Query the user by username
        user = db.query(Registration).filter(Registration.username == username).first()

        if not user:
            logger.warning(f"Get followers failed: User not found - {username}")
            raise HTTPException(status_code=404, detail="User not found")

        # Fetch followers
        followers = db.query(Follows).filter(Follows.following_id == user.user_id).all()
        logger.info(f"Found {len(followers)} followers for user {username}")

        if not followers:
            logger.info(f"No followers found for user {username}")
            raise HTTPException(status_code=404, detail="No followers found")

        # Prepare the response with follower details
        followers_details = []
        for follower in followers:
            follower_user = db.query(Registration).filter(Registration.user_id == follower.follower_id).first()
            if follower_user:
                followers_details.append({
                    "username": follower_user.username,
                    "followed_since": follower.followed_at.strftime("%Y-%m-%d %H:%M:%S")
                })

        execution_time = time.time() - start_time
        logger.info(f"Get followers completed for user {username} in {round(execution_time * 1000, 2)} ms")

        return {"followers": followers_details}

    except HTTPException as he:
        execution_time = time.time() - start_time
        logger.warning(f"HTTP Exception in get followers after {round(execution_time * 1000, 2)} ms: {str(he.detail)}")
        raise he
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Unexpected error in get followers after {round(execution_time * 1000, 2)} ms: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error occurred while fetching followers: {str(e)}")

@router.get("/following/{username}", summary="Get the users that a specific user is following")
def get_following(
    username: str,
    db: Session = Depends(get_db)
):
    """
    Get the list of users that the specified user is following, with details including the date they started following them.
    """
    start_time = time.time()
    logger.info(f"Fetching following list for user: {username}")

    try:
        # Query the user by username
        user = db.query(Registration).filter(Registration.username == username).first()

        if not user:
            logger.warning(f"Get following failed: User not found - {username}")
            raise HTTPException(status_code=404, detail="User not found")

        # Fetch following
        following = db.query(Follows).filter(Follows.follower_id == user.user_id).all()
        logger.info(f"Found {len(following)} users followed by {username}")

        if not following:
            logger.info(f"User {username} is not following anyone")
            raise HTTPException(status_code=404, detail="Not following anyone")

        # Prepare the response with following details
        following_details = []
        for follow in following:
            followed_user = db.query(Registration).filter(Registration.user_id == follow.following_id).first()
            if followed_user:
                following_details.append({
                    "username": followed_user.username,
                    "followed_since": follow.followed_at.strftime("%Y-%m-%d %H:%M:%S")
                })

        execution_time = time.time() - start_time
        logger.info(f"Get following completed for user {username} in {round(execution_time * 1000, 2)} ms")

        return {"following": following_details}

    except HTTPException as he:
        execution_time = time.time() - start_time
        logger.warning(f"HTTP Exception in get following after {round(execution_time * 1000, 2)} ms: {str(he.detail)}")
        raise he
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Unexpected error in get following after {round(execution_time * 1000, 2)} ms: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error occurred while fetching following list: {str(e)}")