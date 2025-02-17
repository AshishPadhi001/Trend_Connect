##Token.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Token(BaseModel):
    token: str
    token_type: str
    expires_in: Optional[int] = None

class TokenData(BaseModel):
    username: str
    id: Optional[int] = None
    issued_at: Optional[datetime] = None
