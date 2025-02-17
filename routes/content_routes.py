#Content_routes.py

from fastapi import APIRouter, HTTPException, status, Depends, File, UploadFile, Form,Query
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
from core.models import Registration,Content,Likes,Comment
from tasks.notify_followers import notify_followers_background

router = APIRouter(
    tags=["Content"]
)

# Directory for saving content files
CONTENT_DIR = "content_database"

# Welcome to the content route
@router.get("/welcome")
def welcome():
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
    try:
        content_info = save_content_to_folder_background(file, username, title, caption)

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

        # Notify followers asynchronously
        notify_followers_background(username, title, caption, db, background_tasks)

        return {"message": "Content created successfully", "content_id": content.c_id}

    except Exception as e:
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
    PAGE_SIZE = 6
    total_content = db.query(Content).count()
    total_pages = (total_content + PAGE_SIZE - 1) // PAGE_SIZE  # Calculate total pages

    # Validate if requested page exists
    if page > total_pages and total_content > 0:
        raise HTTPException(status_code=400, detail="Invalid choice of page")

    offset = (page - 1) * PAGE_SIZE
    content = db.query(Content).offset(offset).limit(PAGE_SIZE).all()

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
    PAGE_SIZE = 6
    # Query content for the given username
    total_content = db.query(Content).filter(Content.username == username).count()
    total_pages = (total_content + PAGE_SIZE - 1) // PAGE_SIZE  # Calculate total pages

    # Validate if requested page exists
    if page > total_pages and total_content > 0:
        raise HTTPException(status_code=400, detail="Invalid choice of page")

    offset = (page - 1) * PAGE_SIZE
    content = db.query(Content).filter(Content.username == username).offset(offset).limit(PAGE_SIZE).all()

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
    # Retrieve content from the database
    content = db.query(models.Content).filter(models.Content.c_id == id).first()
    if not content:
        raise HTTPException(status_code=404, detail=f"No content found with ID {id}")

    # Check if the current user is the content owner
    if content.username != current_user.username:
        raise HTTPException(status_code=403, detail="Not authorized to delete this content")

    try:
        # Delete the content from the database
        db.delete(content)
        db.commit()

        # Trigger the background task to delete the user's folder
        background_tasks.add_task(delete_content_folder_background, content.username)
        
        return {"message": "Content deleted successfully", "id": id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error occurred: {str(e)}")