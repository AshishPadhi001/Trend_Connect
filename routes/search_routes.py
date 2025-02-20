from fastapi import APIRouter, Query, HTTPException, Depends, status
from sqlalchemy.orm import Session
from core.database import get_db
from core.models import Registration
from oauth2 import get_current_user  
from core.models import Content
from Logging.logging import logger
import time

router = APIRouter(
    tags=['Search']
)

@router.get("/search", status_code=status.HTTP_200_OK)
def search_users(
    username: str,
    page: int = Query(1, alias="page", ge=1),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Search users by username with pagination, returning similar usernames in ascending order.
    Default: Page 1, 6 users per page.
    """
    start_time = time.time()
    logger.info(f"User search initiated by {current_user.username} for pattern: '{username}', page: {page}")

    try:
        PAGE_SIZE = 6

        # Query for users whose username is similar
        similar_users = db.query(Registration).filter(Registration.username.ilike(f"%{username}%")).all()
        logger.info(f"Found {len(similar_users)} users matching pattern '{username}'")

        # Sort users by username
        similar_users_sorted = sorted(similar_users, key=lambda x: x.username.lower())

        # Pagination logic
        total_users = len(similar_users_sorted)
        total_pages = (total_users + PAGE_SIZE - 1) // PAGE_SIZE

        # Validate page number
        if page > total_pages and total_users > 0:
            logger.warning(f"Invalid page request: {page} exceeds total pages {total_pages}")
            raise HTTPException(status_code=400, detail="Invalid choice of page")

        # Get paginated users
        offset = (page - 1) * PAGE_SIZE
        paginated_users = similar_users_sorted[offset: offset + PAGE_SIZE]
        logger.info(f"Returning {len(paginated_users)} users for page {page}")

        execution_time = time.time() - start_time
        logger.info(f"User search completed in {round(execution_time * 1000, 2)} ms")

        return {
            "total_users": total_users,
            "total_pages": total_pages,
            "current_page": page,
            "users": [user.username for user in paginated_users],
        }

    except HTTPException as he:
        execution_time = time.time() - start_time
        logger.warning(f"HTTP Exception in user search after {round(execution_time * 1000, 2)} ms: {str(he.detail)}")
        raise he
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Unexpected error in user search after {round(execution_time * 1000, 2)} ms: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error occurred during user search: {str(e)}")

@router.get("/search_by_title", status_code=status.HTTP_200_OK)
def search_content_by_title(
    title: str,
    page: int = Query(1, alias="page", ge=1),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Search content by title or content ID with pagination, returning similar titles in ascending order.
    Default: Page 1, 6 contents per page.
    """
    start_time = time.time()
    search_type = "ID" if title.isdigit() else "title"
    logger.info(f"Content search initiated by {current_user.username} for {search_type}: '{title}', page: {page}")

    try:
        PAGE_SIZE = 6

        # Determine search type and execute query
        if title.isdigit():
            similar_content = db.query(Content).filter(Content.c_id == int(title)).all()
            logger.info(f"Searching for content with ID: {title}")
        else:
            similar_content = db.query(Content).filter(Content.title.ilike(f"%{title}%")).all()
            logger.info(f"Searching for content with title pattern: '{title}'")

        logger.info(f"Found {len(similar_content)} matching content items")

        # Sort content by title
        similar_content_sorted = sorted(similar_content, key=lambda x: x.title.lower())

        # Pagination logic
        total_content = len(similar_content_sorted)
        total_pages = (total_content + PAGE_SIZE - 1) // PAGE_SIZE

        # Validate page number
        if page > total_pages and total_content > 0:
            logger.warning(f"Invalid page request: {page} exceeds total pages {total_pages}")
            raise HTTPException(status_code=400, detail="Invalid choice of page")

        # Get paginated content
        offset = (page - 1) * PAGE_SIZE
        paginated_content = similar_content_sorted[offset: offset + PAGE_SIZE]
        logger.info(f"Returning {len(paginated_content)} content items for page {page}")

        execution_time = time.time() - start_time
        logger.info(f"Content search completed in {round(execution_time * 1000, 2)} ms")

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

    except HTTPException as he:
        execution_time = time.time() - start_time
        logger.warning(f"HTTP Exception in content search after {round(execution_time * 1000, 2)} ms: {str(he.detail)}")
        raise he
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Unexpected error in content search after {round(execution_time * 1000, 2)} ms: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error occurred during content search: {str(e)}")