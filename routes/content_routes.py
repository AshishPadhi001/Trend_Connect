#Content_routes.py

from fastapi import APIRouter, HTTPException, status, Depends, File, UploadFile, Form, Query
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from core import models
from schemas.content import ContentResponse, ContentUpdate, ContentDetailResponse, ContentCreate
from oauth2 import get_current_user  # Ensure the user is authenticated
import os
from datetime import datetime
from fastapi import BackgroundTasks
from tasks.savecontent import save_content_to_folder_background
from tasks.deletecontent import delete_content_folder_background
from core.models import Registration, Content, Likes, Comment
from tasks.notify_followers import notify_followers_background
from Logging.logging import logger
import time

router = APIRouter(
    tags=["Content"]
)

# Directory for saving content files
CONTENT_DIR = "content_database"

# Welcome to the content route
@router.get("/welcome")
def welcome():
    logger.info("Content welcome endpoint accessed")
    return {"message": "Welcome to Content Section of Trend Connect"}

# Create Content
@router.post("/create_content")
async def create_content(
    background_tasks: BackgroundTasks,
    username: str = Form(...),
    title: str = Form(...),
    caption: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: int = Depends(get_current_user)
):
    start_time = time.time()
    logger.info(f"Content creation attempt by user {username}, file: {file.filename}")
    
    try:
        content_info = save_content_to_folder_background(file, username, title, caption)
        logger.info(f"Content saved to folder for user {username}, title: {title}")

        content = models.Content(
            user_id=current_user.user_id,
            username=content_info["username"],
            title=content_info["title"],
            caption=content_info["caption"],
            created_at=content_info["created_at"],
            file=content_info["file"]
        )

        db.add(content)
        db.commit()
        db.refresh(content)
        logger.info(f"Content entry created in database with ID: {content.c_id}")

        # Notify followers asynchronously
        notify_followers_background(username, title, caption, db, background_tasks)
        logger.info(f"Background notification task scheduled for followers of {username}")

        execution_time = time.time() - start_time
        logger.info(f"Content creation completed in {round(execution_time * 1000, 2)} ms")
        
        return {"message": "Content created successfully", "content_id": content.c_id}

    except Exception as e:
        logger.error(f"Error creating content for {username}: {str(e)}")
        return {"message": "Error creating content", "error": str(e)}


#GEt all content
@router.get("/get_content", status_code=status.HTTP_200_OK)
def get_all_content(
    page: int = Query(1, alias="page", ge=1),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),  # Ensure the user is authenticated
):
    """
    Retrieve paginated content, including total likes and associated comments.
    Default: Page 1, 6 posts per page.
    """
    start_time = time.time()
    logger.info(f"Get all content request from user {current_user.username}, page: {page}")
    
    PAGE_SIZE = 6
    total_content = db.query(Content).count()
    total_pages = (total_content + PAGE_SIZE - 1) // PAGE_SIZE  # Calculate total pages

    # Validate if requested page exists
    if page > total_pages and total_content > 0:
        logger.warning(f"Invalid page request: {page} exceeds total pages {total_pages}")
        raise HTTPException(status_code=400, detail="Invalid choice of page")

    offset = (page - 1) * PAGE_SIZE
    content = db.query(Content).offset(offset).limit(PAGE_SIZE).all()
    logger.info(f"Retrieved {len(content)} content items for page {page}")

    content_details = []
    for c in content:
        likes_count = db.query(Likes).filter(Likes.post_id == c.c_id).count()
        comments = db.query(Comment).filter(Comment.post_id == c.c_id).all()
        comment_texts = [comment.user_comment for comment in comments]

        content_details.append(ContentDetailResponse(
            username=c.username,
            title=c.title,
            caption=c.caption,
            created_at=c.created_at,
            comments=comment_texts,
            total_likes=likes_count
        ))

    execution_time = time.time() - start_time
    logger.info(f"Get all content completed in {round(execution_time * 1000, 2)} ms")
    
    return {
        "content": content_details,
        "total_content": total_content,
        "total_pages": total_pages,
        "current_page": page
    }

# Get content by username with pagination and authentication
@router.get("/get_content_by_username", status_code=status.HTTP_200_OK)
def get_content_by_username(
    username: str,
    page: int = Query(1, alias="page", ge=1),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),  # Ensure the user is authenticated
):
    """
    Retrieve paginated content by username, including total likes and associated comments.
    Default: Page 1, 6 posts per page.
    """
    start_time = time.time()
    logger.info(f"Get content by username request from {current_user.username} for user {username}, page: {page}")
    
    PAGE_SIZE = 6
    # Query content for the given username
    total_content = db.query(Content).filter(Content.username == username).count()
    total_pages = (total_content + PAGE_SIZE - 1) // PAGE_SIZE  # Calculate total pages

    # Validate if requested page exists
    if page > total_pages and total_content > 0:
        logger.warning(f"Invalid page request: {page} exceeds total pages {total_pages} for user {username}")
        raise HTTPException(status_code=400, detail="Invalid choice of page")

    offset = (page - 1) * PAGE_SIZE
    content = db.query(Content).filter(Content.username == username).offset(offset).limit(PAGE_SIZE).all()
    logger.info(f"Retrieved {len(content)} content items for user {username}, page {page}")

    content_details = []
    for c in content:
        likes_count = db.query(Likes).filter(Likes.post_id == c.c_id).count()
        comments = db.query(Comment).filter(Comment.post_id == c.c_id).all()
        comment_texts = [comment.user_comment for comment in comments]

        content_details.append(ContentDetailResponse(
            username=c.username,
            title=c.title,
            caption=c.caption,
            created_at=c.created_at,
            comments=comment_texts,
            total_likes=likes_count
        ))

    execution_time = time.time() - start_time
    logger.info(f"Get content by username completed in {round(execution_time * 1000, 2)} ms")
    
    return {
        "content": content_details,
        "total_content": total_content,
        "total_pages": total_pages,
        "current_page": page
    }


# Delete content by ID
@router.delete("/delete_content/{id}", status_code=status.HTTP_200_OK)
def delete_content_by_id(
    id: int, 
    db: Session = Depends(get_db), 
    current_user: str = Depends(get_current_user), 
    background_tasks: BackgroundTasks = BackgroundTasks()  # Corrected this line
):
    start_time = time.time()
    logger.info(f"Delete content request from {current_user.username} for content ID: {id}")
    
    # Retrieve content from the database
    content = db.query(models.Content).filter(models.Content.c_id == id).first()
    if not content:
        logger.warning(f"Content not found: ID {id} requested by {current_user.username}")
        raise HTTPException(status_code=404, detail=f"No content found with ID {id}")

    # Check if the current user is the content owner
    if content.username != current_user.username:
        logger.warning(f"Unauthorized deletion attempt: {current_user.username} tried to delete content {id} owned by {content.username}")
        raise HTTPException(status_code=403, detail="Not authorized to delete this content")

    try:
        # Delete the content from the database
        db.delete(content)
        db.commit()
        logger.info(f"Content {id} deleted from database by {current_user.username}")

        # Trigger the background task to delete the user's folder
        background_tasks.add_task(delete_content_folder_background, content.username)
        logger.info(f"Background task scheduled to delete content folder for {content.username}")
        
        execution_time = time.time() - start_time
        logger.info(f"Delete content completed in {round(execution_time * 1000, 2)} ms")
        
        return {"message": "Content deleted successfully", "id": id}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting content {id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error occurred: {str(e)}")