##Profile_routes.py

from fastapi import FastAPI, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from core.models import Registration, Content, Likes, Comment, Follows
from schemas.profile import UserProfileResponse, ContentDetailResponse
from core.database import get_db
from utils.hashing import verify

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
    # Query the user by username
    user = db.query(Registration).filter(Registration.username == user_credential.username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate the password (compare hashed password with plain password)
    if not verify(user_credential.password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect password")

    # Count followers and following
    followers_count = db.query(Follows).filter(Follows.following_id == user.user_id).count()
    following_count = db.query(Follows).filter(Follows.follower_id == user.user_id).count()

    # Prepare user profile response
    user_profile = {
        "username": user.username,
        "followers": followers_count,
        "following": following_count,
        "content": []
    }

    # Fetch the user's content
    content_list = db.query(Content).filter(Content.username == user.username).all()

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

    return user_profile

# Route to get users who follow a specific user
@router.get("/followers/{username}", summary="Get the users who follow a specific user")
def get_followers(
    username: str,
    db: Session = Depends(get_db)
):
    """
    Get the list of users who follow the specified user, with details including the date they followed.
    """
    # Query the user by username
    user = db.query(Registration).filter(Registration.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch followers (those who follow the user)
    followers = db.query(Follows).filter(Follows.following_id == user.user_id).all()

    if not followers:
        raise HTTPException(status_code=404, detail="No followers found")

    # Prepare the response with follower details
    followers_details = []
    for follower in followers:
        follower_user = db.query(Registration).filter(Registration.user_id == follower.follower_id).first()
        if follower_user:
            followers_details.append({
                "username": follower_user.username,
                "followed_since": follower.followed_at.strftime("%Y-%m-%d %H:%M:%S")  # You can adjust the datetime format as needed
            })

    return {"followers": followers_details}


# Route to get users who the current user is following
@router.get("/following/{username}", summary="Get the users that a specific user is following")
def get_following(
    username: str,
    db: Session = Depends(get_db)
):
    """
    Get the list of users that the specified user is following, with details including the date they started following them.
    """
    # Query the user by username
    user = db.query(Registration).filter(Registration.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch following (those the user is following)
    following = db.query(Follows).filter(Follows.follower_id == user.user_id).all()

    if not following:
        raise HTTPException(status_code=404, detail="Not following anyone")

    # Prepare the response with following details
    following_details = []
    for follow in following:
        followed_user = db.query(Registration).filter(Registration.user_id == follow.following_id).first()
        if followed_user:
            following_details.append({
                "username": followed_user.username,
                "followed_since": follow.followed_at.strftime("%Y-%m-%d %H:%M:%S")  # Adjust format as needed
            })

    return {"following": following_details}