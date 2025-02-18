from fastapi import FastAPI
from core import database, models  
import routes.auth_routes as auth_routes
import routes.user_routes as user_routes
import routes.content_routes as content_routes
import routes.likes_routes as likes_routes
import routes.comments_routes as comments_routes
import routes.search_routes as search_routes
import routes.profile_routes as profile_routes
import routes.follow_routes as follow_routes

app = FastAPI(
    title="Trend Connect",
    version="1.0.0",
)

# Create the database tables
models.Base.metadata.create_all(bind=database.engine)  # Ensure models.Base is set up properly

# Register API router for login
app.include_router(auth_routes.router)

# Register API Router for User
app.include_router(user_routes.router)

# Register API router for content
app.include_router(content_routes.router)

# Register API router for likes
app.include_router(likes_routes.router)

# Register API Router for comments
app.include_router(comments_routes.router)

# Register API Router for Search
app.include_router(search_routes.router)

# Register API Routes for profile
app.include_router(profile_routes.router)

# Register API Routes for Follow / Unfollow
app.include_router(follow_routes.router)

#HEalth check
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "TrendConnect"}

