##search_routes.py

from fastapi import APIRouter, Query, HTTPException, Depends, status
from sqlalchemy.orm import Session
from core.database import get_db
from core.models import Registration
from oauth2 import get_current_user  
from core.models import Content

router = APIRouter(
    tags=['Search']
)

# Search for users by username with pagination and authentication
@router.get("/search", status_code=status.HTTP_200_OK)
def search_users(
    username: str,
    page: int = Query(1, alias="page", ge=1),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),  # Ensure the user is authenticated
):
    """
    Search users by username with pagination, returning similar usernames in ascending order.
    Default: Page 1, 6 users per page.
    """
    PAGE_SIZE = 6

    # Query for users whose username is similar to the provided username (case-insensitive search)
    similar_users = db.query(Registration).filter(Registration.username.ilike(f"%{username}%")).all()

    # Sort users by username in ascending order
    similar_users_sorted = sorted(similar_users, key=lambda x: x.username.lower())

    # Pagination logic
    total_users = len(similar_users_sorted)
    total_pages = (total_users + PAGE_SIZE - 1) // PAGE_SIZE  # Calculate total pages

    # Validate if requested page exists
    if page > total_pages and total_users > 0:
        raise HTTPException(status_code=400, detail="Invalid choice of page")

    # Get the users for the requested page
    offset = (page - 1) * PAGE_SIZE
    paginated_users = similar_users_sorted[offset: offset + PAGE_SIZE]

    # Return the response with the list of similar usernames and pagination data
    return {
        "total_users": total_users,
        "total_pages": total_pages,
        "current_page": page,
        "users": [user.username for user in paginated_users],
    }


# Search for content by title with pagination and authentication
@router.get("/search_by_title", status_code=status.HTTP_200_OK)
def search_content_by_title(
    title: str,
    page: int = Query(1, alias="page", ge=1),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),  # Ensure the user is authenticated
):
    """
    Search content by title or content ID with pagination, returning similar titles in ascending order.
    Default: Page 1, 6 contents per page.
    """
    PAGE_SIZE = 6

    # Check if the title is numeric (e.g., age or content ID), and adjust the query accordingly
    if title.isdigit():
        # If the title is a number, assume it's an ID and search by content ID
        similar_content = db.query(Content).filter(Content.c_id == int(title)).all()
    else:
        # If it's not a number, search by title (case-insensitive search)
        similar_content = db.query(Content).filter(Content.title.ilike(f"%{title}%")).all()

    # Sort content by title in ascending order
    similar_content_sorted = sorted(similar_content, key=lambda x: x.title.lower())

    # Pagination logic
    total_content = len(similar_content_sorted)
    total_pages = (total_content + PAGE_SIZE - 1) // PAGE_SIZE  # Calculate total pages

    # Validate if requested page exists
    if page > total_pages and total_content > 0:
        raise HTTPException(status_code=400, detail="Invalid choice of page")

    # Get the content for the requested page
    offset = (page - 1) * PAGE_SIZE
    paginated_content = similar_content_sorted[offset: offset + PAGE_SIZE]

    # Return the response with the list of similar titles and pagination data
    return {
        "total_content": total_content,
        "total_pages": total_pages,
        "current_page": page,
        "content": [
            {
                "title": c.title,
                "username": c.username,
                "created_at": c.created_at,
            } for c in paginated_content
        ],
    }