import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from core.models import Registration, Content, Likes, Comment, Follows
from schemas.profile import UserProfileResponse, ContentDetailResponse
from routes.profile_routes import profile_login, get_followers, get_following

class TestProfileRoutes(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        self.db = Mock(spec=Session)
        self.mock_user = Mock(spec=Registration)
        self.mock_user.user_id = 1
        self.mock_user.username = "testuser"
        self.mock_user.password = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewfJWQq.pzXP.4Om"  # Hashed "password123"

    @patch('routers.profile.verify')
    def test_profile_login_success(self, mock_verify):
        """Test successful profile login"""
        # Arrange
        mock_verify.return_value = True
        credentials = OAuth2PasswordRequestForm(username="testuser", password="password123", scope="")
        
        # Mock database queries
        self.db.query.return_value.filter.return_value.first.side_effect = [
            self.mock_user,  # User query
        ]
        
        # Mock counts and content
        self.db.query.return_value.filter.return_value.count.side_effect = [2, 3]  # followers, following
        
        mock_content = Mock(spec=Content)
        mock_content.username = "testuser"
        mock_content.title = "Test Post"
        mock_content.caption = "Test Caption"
        mock_content.created_at = datetime.now()
        mock_content.c_id = 1
        
        self.db.query.return_value.filter.return_value.all.side_effect = [
            [mock_content],  # Content query
            [],  # Comments query
        ]
        
        # Act
        result = profile_login(user_credential=credentials, db=self.db)

        # Assert
        self.assertEqual(result["username"], "testuser")
        self.assertEqual(result["followers"], 2)
        self.assertEqual(result["following"], 3)
        self.assertTrue(isinstance(result["content"], list))

    def test_profile_login_user_not_found(self):
        """Test profile login with non-existent user"""
        # Arrange
        credentials = OAuth2PasswordRequestForm(username="nonexistent", password="password123", scope="")
        self.db.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            profile_login(user_credential=credentials, db=self.db)
        
        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "User not found")

    @patch('routers.profile.verify')
    def test_profile_login_incorrect_password(self, mock_verify):
        """Test profile login with incorrect password"""
        # Arrange
        mock_verify.return_value = False
        credentials = OAuth2PasswordRequestForm(username="testuser", password="wrongpassword", scope="")
        self.db.query.return_value.filter.return_value.first.return_value = self.mock_user

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            profile_login(user_credential=credentials, db=self.db)
        
        self.assertEqual(context.exception.status_code, 401)
        self.assertEqual(context.exception.detail, "Incorrect password")

    def test_get_followers_success(self):
        """Test successful retrieval of followers"""
        # Arrange
        mock_follower = Mock(spec=Follows)
        mock_follower.follower_id = 2
        mock_follower.followed_at = datetime.now()

        mock_follower_user = Mock(spec=Registration)
        mock_follower_user.username = "follower1"

        self.db.query.return_value.filter.return_value.first.side_effect = [
            self.mock_user,  # User query
            mock_follower_user,  # Follower user query
        ]
        self.db.query.return_value.filter.return_value.all.return_value = [mock_follower]

        # Act
        result = get_followers(username="testuser", db=self.db)

        # Assert
        self.assertTrue("followers" in result)
        self.assertEqual(len(result["followers"]), 1)
        self.assertEqual(result["followers"][0]["username"], "follower1")

    def test_get_followers_user_not_found(self):
        """Test get followers with non-existent user"""
        # Arrange
        self.db.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            get_followers(username="nonexistent", db=self.db)
        
        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "User not found")

    def test_get_following_success(self):
        """Test successful retrieval of following users"""
        # Arrange
        mock_following = Mock(spec=Follows)
        mock_following.following_id = 2
        mock_following.followed_at = datetime.now()

        mock_followed_user = Mock(spec=Registration)
        mock_followed_user.username = "followed1"

        self.db.query.return_value.filter.return_value.first.side_effect = [
            self.mock_user,  # User query
            mock_followed_user,  # Followed user query
        ]
        self.db.query.return_value.filter.return_value.all.return_value = [mock_following]

        # Act
        result = get_following(username="testuser", db=self.db)

        # Assert
        self.assertTrue("following" in result)
        self.assertEqual(len(result["following"]), 1)
        self.assertEqual(result["following"][0]["username"], "followed1")

    def test_get_following_user_not_found(self):
        """Test get following with non-existent user"""
        # Arrange
        self.db.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            get_following(username="nonexistent", db=self.db)
        
        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "User not found")

    def test_get_following_no_following(self):
        """Test get following when user isn't following anyone"""
        # Arrange
        self.db.query.return_value.filter.return_value.first.return_value = self.mock_user
        self.db.query.return_value.filter.return_value.all.return_value = []

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            get_following(username="testuser", db=self.db)
        
        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "Not following anyone")

if __name__ == '__main__':
    unittest.main()