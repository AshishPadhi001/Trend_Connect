from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from core.database import get_db
from utils.hashing import verify
from core import models
from oauth2 import create_tokens
import warnings
from Logging.logging import logger
import time
warnings.filterwarnings('ignore')

router = APIRouter(tags=["Authentication"])


@router.get("/login_welcome", summary="Welcome to Login Section")
def welcome():
    logger.info("Login welcome endpoint accessed")
    return {"message": "Welcome to Login Section of Trend Connect"}

@router.post("/login", response_model=dict, summary="Login of registered user")
def login(
    user_credential: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    start_time = time.time()
    logger.info(f"Login attempt for username: {user_credential.username}")
    
    # Fetch user by username
    user = db.query(models.Registration).filter(
        models.Registration.username == user_credential.username
    ).first()

    # Validate user existence
    if not user:
        logger.warning(f"Login failed: No user found with username {user_credential.username}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No user found with username {user_credential.username}. Go and register yourself first"
        )

    # Verify password
    if not verify(user_credential.password, user.password):
        logger.warning(f"Login failed: Incorrect password for user {user_credential.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    # Generate token with additional user info
    token = create_tokens({
        "username": user_credential.username,
        "user_id": user.user_id
    })

    # Log successful login
    execution_time = time.time() - start_time
    logger.info(f"Login successful for user: {user_credential.username} | User ID: {user.user_id} | Time: {round(execution_time * 1000, 2)} ms")
    
    # Return login response
    return {
        "message": "Login successful",
        "token": token,
        "token_type": "bearer",
        "user_id": user.user_id
    }

@router.post("/logout", summary="Logout the user")
def logout():
    # In JWT, logout is handled client-side by token removal
    logger.info("User logout endpoint accessed")
    return {
        "message": "You have been logged out. Please remove the token from your client-side storage."
    }