import unittest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from core.models import Registration, Follows
from routes.follow_routes import follow_user, unfollow_user
from schemas.follow import FollowRequest

class TestFollowRoutes(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.db = MagicMock(spec=Session)
        self.current_user = Registration(
            user_id=1,
            username="test_user"
        )
        self.target_user = Registration(
            user_id=2,
            username="target_user"
        )
        
        # Common test data
        self.follow_request = FollowRequest(user_id=2)  # Request to follow user_id 2
        
        # Mock follow entry
        self.mock_follow = Follows(
            follower_id=self.current_user.user_id,
            following_id=self.target_user.user_id,
            followed_at=datetime.utcnow()
        )

    def test_follow_user_success(self):
        """Test successful follow operation."""
        # Arrange
        self.db.query(Registration).filter_by().first.return_value = self.target_user
        self.db.query(Follows).filter_by().first.return_value = None  # No existing follow

        # Act
        response = follow_user(
            request=self.follow_request,
            current_user=self.current_user,
            db=self.db
        )

        # Assert
        self.assertEqual(response["message"], "Followed successfully")
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_follow_self(self):
        """Test attempting to follow oneself."""
        # Arrange
        self.follow_request.user_id = self.current_user.user_id

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            follow_user(
                request=self.follow_request,
                current_user=self.current_user,
                db=self.db
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "You cannot follow yourself")
        self.db.add.assert_not_called()

    def test_follow_nonexistent_user(self):
        """Test attempting to follow a user that doesn't exist."""
        # Arrange
        self.db.query(Registration).filter_by().first.return_value = None

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            follow_user(
                request=self.follow_request,
                current_user=self.current_user,
                db=self.db
            )

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "User to follow not found")
        self.db.add.assert_not_called()

    def test_follow_already_following(self):
        """Test attempting to follow a user that is already being followed."""
        # Arrange
        self.db.query(Registration).filter_by().first.return_value = self.target_user
        self.db.query(Follows).filter_by().first.return_value = self.mock_follow

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            follow_user(
                request=self.follow_request,
                current_user=self.current_user,
                db=self.db
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "You are already following this user")
        self.db.add.assert_not_called()

    def test_unfollow_user_success(self):
        """Test successful unfollow operation."""
        # Arrange
        self.db.query(Follows).filter_by().first.return_value = self.mock_follow

        # Act
        response = unfollow_user(
            request=self.follow_request,
            current_user=self.current_user,
            db=self.db
        )

        # Assert
        self.assertEqual(response["message"], "Unfollowed successfully")
        self.db.delete.assert_called_once_with(self.mock_follow)
        self.db.commit.assert_called_once()

    def test_unfollow_not_following(self):
        """Test attempting to unfollow a user that is not being followed."""
        # Arrange
        self.db.query(Follows).filter_by().first.return_value = None

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            unfollow_user(
                request=self.follow_request,
                current_user=self.current_user,
                db=self.db
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "You are not following this user")
        self.db.delete.assert_not_called()

    def test_follow_database_error(self):
        """Test handling of database errors during follow operation."""
        # Arrange
        self.db.query(Registration).filter_by().first.return_value = self.target_user
        self.db.query(Follows).filter_by().first.return_value = None
        self.db.commit.side_effect = Exception("Database error")

        # Act & Assert
        with self.assertRaises(Exception) as context:
            follow_user(
                request=self.follow_request,
                current_user=self.current_user,
                db=self.db
            )

        self.assertEqual(str(context.exception), "Database error")

    def test_unfollow_database_error(self):
        """Test handling of database errors during unfollow operation."""
        # Arrange
        self.db.query(Follows).filter_by().first.return_value = self.mock_follow
        self.db.commit.side_effect = Exception("Database error")

        # Act & Assert
        with self.assertRaises(Exception) as context:
            unfollow_user(
                request=self.follow_request,
                current_user=self.current_user,
                db=self.db
            )

        self.assertEqual(str(context.exception), "Database error")

if __name__ == '__main__':
    unittest.main()