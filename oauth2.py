from datetime import datetime, timedelta
from schemas.token import Token, TokenData
from core import database, models
from sqlalchemy.orm import Session
from configuration.config import settings
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

# OAuth2PasswordBearer: Extracts the token from the request header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Secret Key for JWT encoding
secret_key = settings.SECRET_KEY
algorithm = settings.ALGORITHM
expire_time_minutes = settings.ACCESS_TOKEN_EXPIRY_MINUTES

def create_tokens(data: dict):
    """
    Creates a JWT token with the given data and expiration time.
    """
    to_encode = data.copy()
    
    # Set expiration time
    expire = datetime.utcnow() + timedelta(minutes=expire_time_minutes)
    
    # Update payload with expiration, subject, and issued at time
    to_encode.update({
        "exp": expire, 
        "sub": data["username"],  # Use username as subject
        "iat": datetime.utcnow()  # Issued at time
    })
    
    # Encode the token using the secret key and algorithm
    tokens = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    
    return tokens

def verify_token(token: str, credential_exception):
    """
    Verifies the given JWT token.
    Decodes the token and checks its validity (expiration, username).
    """
    try:
        # Decode the token with the specified algorithm
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        
        # Extract username and validate
        username: str = payload.get("sub")
        if not username:
            raise credential_exception
        
        # Return token data with username and user_id
        return TokenData(
            username=username, 
            id=payload.get("user_id"),  # Optional: include user_id if available
            issued_at=payload.get("iat")
        )
    except JWTError:
        # Handle any errors during token validation
        raise credential_exception

def get_current_user(db: Session = Depends(database.get_db), token: str = Depends(oauth2_scheme)):
    """
    Extracts the current user from the provided JWT token.
    Validates the token and fetches user details from the database.
    """
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    
    try:
        # Decode the token to extract user details
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        username: str = payload.get("sub")
        
        if username is None:
            raise credential_exception
        
        # Fetch the user from the database based on the username
        user = db.query(models.Registration).filter(models.Registration.username == username).first()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user  # Return the user object
    
    except JWTError:
        # Handle invalid token error
        raise credential_exception
