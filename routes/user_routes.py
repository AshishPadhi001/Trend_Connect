#User_routes.py

# Standard imports
from datetime import datetime, timedelta
from typing import List, Optional

# FastAPI specific imports
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks,Query

# Database and Models
from sqlalchemy.orm import Session
from core.database import get_db
from core.models import Registration
from core import models

# Pydantic models for validation
from pydantic import BaseModel, EmailStr
from schemas.registration import RegisterUser, VerifyOTP, RegistrationResponse, RegisterUserDetails
from schemas.profile import UserProfileResponse

# Utility functions and services
from utils.hashing import hashing, generate_otp
from utils.email_service import send_email
from utils.sms_service import send_sms

# OAuth2 and current user authentication
from oauth2 import get_current_user

# Background tasks
from tasks.deleteemail import send_deletion_email_background
from tasks.updateemail import send_update_email_background
from tasks.send_otp_task import send_otp_background
from tasks.age_diff import age_difference
from tasks.check_password import check_password_strength
from tasks.check_phone import validate_phone_number


# Twilio for SMS (if you're using it)
from twilio.rest import Client

# Configuration settings
from configuration.config import settings


router = APIRouter(tags=["SignUp"])

OTP_EXPIRATION_MINUTES = 10
MINIMUM_AGE_YEARS = 14

@router.post("/register/send_otp")
async def send_otp(user: RegisterUser, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):

    existing_user = db.query(Registration).filter(Registration.email == user.email).first()
    otp = generate_otp()
    expiry_time = datetime.utcnow() + timedelta(minutes=OTP_EXPIRATION_MINUTES)
    
    if existing_user:
        if existing_user.is_active:
            raise HTTPException(status_code=226, detail=f"User with email {user.email} is already registered")
        
        existing_user.otp = otp
        existing_user.otp_expiry = expiry_time
        existing_user.retry_attempts += 1
    else:
        temp_user = Registration(
            email=user.email,
            otp=otp,
            otp_expiry=expiry_time,
            retry_attempts=1,
            created_at=datetime.utcnow(),
            is_active=False
        )
        db.add(temp_user)
    
    background_tasks.add_task(send_otp_background, user.email, otp)

    db.commit()
    return {"message": f"OTP sent successfully to {user.email}. Please verify your OTP."}
# Step 2: Verify OTP and activate the user
@router.post("/register/verify_otp")
def verify_otp(data: VerifyOTP, db: Session = Depends(get_db)):
    user = db.query(Registration).filter(Registration.email == data.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")
    
    # Check OTP validity
    if not user.otp == data.otp:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP")

    if datetime.utcnow() > user.otp_expiry:
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")

    # OTP verified successfully, user remains inactive for now
    return {"message": "OTP verified successfully. Please complete your registration details."}


#registration of user
@router.post("/register/complete_registration", response_model=RegistrationResponse)
async def complete_registration(user_details: RegisterUserDetails, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(Registration).filter(Registration.email == user_details.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="User does not exist. Please verify your OTP first.")
    
    if user.is_active:
        raise HTTPException(status_code=208, detail="User is already registered.")
    
    # Add background tasks for age verification
    background_tasks.add_task(age_difference, user_details.dob)

    # Add background task for password strength verification
    background_tasks.add_task(check_password_strength, user_details.password)

    # Add background task for phone number validation
    background_tasks.add_task(validate_phone_number, user_details.phone_number)

    # Age verification (synchronous, you can modify this to run in the background if necessary)
    years, months, days, hours, minutes = age_difference(user_details.dob)
    if years < MINIMUM_AGE_YEARS:
        raise HTTPException(
            status_code=406,
            detail=f"User is too young to register. Must be at least {MINIMUM_AGE_YEARS} years old."
        )

    # Password strength verification (synchronous, you can modify this to run in the background if necessary)
    password_strength = check_password_strength(user_details.password)
    if password_strength in ["low", "medium"]:
        raise HTTPException(status_code=406, detail=f"Password strength is too {password_strength}. Please use a stronger password.")

    # Phone number validation (synchronous, you can modify this to run in the background if necessary)
    if not validate_phone_number(user_details.phone_number):
        raise HTTPException(status_code=406, detail="Invalid phone number. It must be exactly 10 digits.")

    # Store hashed password
    hashed_password = hashing(user_details.password)
    user.username = user_details.username
    user.password = hashed_password
    user.phone_number = user_details.phone_number
    user.country = user_details.country
    user.dob = user_details.dob
    user.is_active = True  # Activate user
    db.commit()

    return RegistrationResponse(user_id=user.user_id, username=user.username)


# Fetch all users with followers and following counts
@router.get("/get_users", status_code=status.HTTP_200_OK)
def get_all_users(page: int = Query(1, alias="page", ge=1), db: Session = Depends(get_db)):
    """
    Retrieve paginated users with followers and following counts.
    Default: Page 1, 3 users per page.
    """
    PAGE_SIZE = 3
    total_users = db.query(models.Registration).count()
    total_pages = (total_users + PAGE_SIZE - 1) // PAGE_SIZE  # Calculate total pages

    # Validate if requested page exists
    if page > total_pages and total_users > 0:
        raise HTTPException(status_code=400, detail="Invalid choice of page")

    offset = (page - 1) * PAGE_SIZE
    users = db.query(models.Registration).offset(offset).limit(PAGE_SIZE).all()

    users_with_follow_counts = []
    
    for user in users:
        # Count followers and following
        followers_count = db.query(models.Follows).filter(models.Follows.following_id == user.user_id).count()
        following_count = db.query(models.Follows).filter(models.Follows.follower_id == user.user_id).count()
        
        # Prepare user profile with followers and following counts
        user_profile = {
            "username": user.username,
            "followers": followers_count,
            "following": following_count
        }
        
        users_with_follow_counts.append(user_profile)

    return {
        "users": users_with_follow_counts,
        "total_users": total_users,
        "total_pages": total_pages,
        "current_page": page
    }

# Fetch a specific user by ID with followers and following counts
@router.get("/get_user/{user_id}", response_model=UserProfileResponse)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Count followers and following
    followers_count = db.query(models.Follows).filter(models.Follows.following_id == user.user_id).count()
    following_count = db.query(models.Follows).filter(models.Follows.follower_id == user.user_id).count()
    
    # Prepare response
    user_profile = {
        "username": user.username,
        "followers": followers_count,
        "following": following_count
    }

    return user_profile

# Update user details
@router.put("/update_user/{user_id}", response_model=RegistrationResponse)
async def update_user(
    background_tasks: BackgroundTasks,
    user_id: int, 
    updated_user: RegisterUser, 
    db: Session = Depends(get_db), 
    current_user: str = Depends(get_current_user)
):
    user = db.query(Registration).filter(Registration.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user.username != user.username:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")

    # Store old email in case it's being updated
    old_email = user.email

    # Update user details
    user.username = updated_user.username if updated_user.username else user.username
    user.dob = updated_user.dob if updated_user.dob else user.dob
    user.phone_number = updated_user.phone_number if updated_user.phone_number else user.phone_number
    user.email = updated_user.email if updated_user.email else user.email
    user.country = updated_user.country if updated_user.country else user.country

    if updated_user.password:
        user.password = hashing(updated_user.password)

    db.commit()
    db.refresh(user)

    # Add email sending to background tasks
    email_to_use = old_email if updated_user.email else user.email
    background_tasks.add_task(send_update_email_background, email_to_use, user.username)

    return user

#Delete the user
@router.delete("/delete_user/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    background_tasks: BackgroundTasks,
    user_id: int, 
    db: Session = Depends(get_db), 
    current_user: str = Depends(get_current_user)
):
    user = db.query(Registration).filter(Registration.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user.username != user.username:
        raise HTTPException(status_code=403, detail="Not authorized to delete this user")

    # Store user info before deletion
    user_email = user.email
    user_username = user.username

    # Delete the user
    db.delete(user)
    db.commit()

    # Add email sending to background tasks
    background_tasks.add_task(send_deletion_email_background, user_email, user_username)

    return {"message": "User deleted successfully"}