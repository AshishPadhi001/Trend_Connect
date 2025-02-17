from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base
import warnings
warnings.filterwarnings('ignore')

class Registration(Base):
    __tablename__ = "registrations"
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    email = Column(String, unique=True, index=True)
    dob = Column(Date)
    phone_number = Column(String)
    country = Column(String)
    is_active = Column(Boolean, default=False)
    otp = Column(Integer, nullable=True)
    otp_expiry = Column(DateTime, nullable=True)
    retry_attempts = Column(Integer, default=0)
    created_at = Column(Date, default=datetime.utcnow)

    content = relationship("Content", back_populates="owner")
    likes = relationship("Likes", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    
    followers = relationship("Follows", foreign_keys="Follows.following_id", back_populates="following", cascade="all, delete-orphan")
    following = relationship("Follows", foreign_keys="Follows.follower_id", back_populates="follower", cascade="all, delete-orphan")

class Content(Base):
    __tablename__ = "content"
    c_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("registrations.user_id"))
    username = Column(String)
    title = Column(String)
    caption = Column(String)
    file = Column(String)
    created_at = Column(Date, default=datetime.utcnow)

    owner = relationship("Registration", back_populates="content")
    likes = relationship("Likes", back_populates="content")
    comments = relationship("Comment", back_populates="content")

class Likes(Base):
    __tablename__ = "likes"
    like_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("registrations.user_id"))
    post_id = Column(Integer, ForeignKey("content.c_id"))

    user = relationship("Registration", back_populates="likes")
    content = relationship("Content", back_populates="likes")

class Comment(Base):
    __tablename__ = "comments"
    comment_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("registrations.user_id"))
    post_id = Column(Integer, ForeignKey("content.c_id"))
    user_comment = Column(String)

    user = relationship("Registration", back_populates="comments")
    content = relationship("Content", back_populates="comments")

class Follows(Base):
    __tablename__ = "follows"
    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("registrations.user_id"), nullable=False)
    following_id = Column(Integer, ForeignKey("registrations.user_id"), nullable=False)
    followed_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint('follower_id', 'following_id', name='unique_follow'),)
    
    follower = relationship("Registration", foreign_keys=[follower_id], back_populates="following")
    following = relationship("Registration", foreign_keys=[following_id], back_populates="followers")