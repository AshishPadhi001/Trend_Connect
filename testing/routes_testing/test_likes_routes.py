import unittest
from unittest.mock import Mock, patch
from fastapi import HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from core import models
from schemas.likes import LikeInput
from routes.likes_routes import manage_likes  # Updated import path

class TestLikeEndpoint(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        self.db = Mock(spec=Session)
        self.current_user = Mock()
        self.current_user.user_id = 1
        self.current_user.username = "testuser"
        self.background_tasks = Mock(spec=BackgroundTasks)

    @patch('routes.likes_routes.models.Content')  # Updated patch path
    @patch('routes.likes_routes.models.Likes')    # Updated patch path
    def test_like_post_success(self, mock_likes_model, mock_content_model):
        """Test successful post like"""
        # Arrange
        like_input = LikeInput(post_id=1, dir=1)
        
        # Mock the database queries
        mock_post = Mock()
        mock_post.c_id = 1
        mock_post.owner_id = 2
        
        # Set up the chain of mock returns
        self.db.query.return_value.filter.return_value.first.side_effect = [
            mock_post,  # Post exists
            None        # Like doesn't exist yet
        ]

        # Act
        result = manage_likes(
            background_tasks=self.background_tasks,
            like=like_input,
            db=self.db,
            current_user=self.current_user
        )

        # Assert
        self.assertEqual(result, {"message": "Post liked successfully"})
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.background_tasks.add_task.assert_called_once()

    @patch('routes.likes_routes.models.Content')  # Updated patch path
    @patch('routes.likes_routes.models.Likes')    # Updated patch path
    def test_unlike_post_success(self, mock_likes_model, mock_content_model):
        """Test successful post unlike"""
        # Arrange
        like_input = LikeInput(post_id=1, dir=0)
        
        mock_post = Mock()
        mock_post.c_id = 1
        
        mock_like = Mock()
        mock_like.user_id = self.current_user.user_id
        mock_like.post_id = like_input.post_id

        self.db.query.return_value.filter.return_value.first.side_effect = [
            mock_post,  # Post exists
            mock_like   # Like exists
        ]

        # Act
        result = manage_likes(
            background_tasks=self.background_tasks,
            like=like_input,
            db=self.db,
            current_user=self.current_user
        )

        # Assert
        self.assertEqual(result, {"message": "Post unliked successfully"})
        self.db.delete.assert_called_once_with(mock_like)
        self.db.commit.assert_called_once()

    @patch('routes.likes_routes.models.Content')  # Updated patch path
    def test_like_nonexistent_post(self, mock_content_model):
        """Test liking a post that doesn't exist"""
        # Arrange
        like_input = LikeInput(post_id=999, dir=1)
        self.db.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            manage_likes(
                background_tasks=self.background_tasks,
                like=like_input,
                db=self.db,
                current_user=self.current_user
            )
        
        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "No post found")

    @patch('routes.likes_routes.models.Content')  # Updated patch path
    @patch('routes.likes_routes.models.Likes')    # Updated patch path
    def test_like_already_liked_post(self, mock_likes_model, mock_content_model):
        """Test liking a post that's already been liked"""
        # Arrange
        like_input = LikeInput(post_id=1, dir=1)
        
        mock_post = Mock()
        mock_post.c_id = 1
        
        mock_existing_like = Mock()
        mock_existing_like.user_id = self.current_user.user_id
        mock_existing_like.post_id = like_input.post_id

        self.db.query.return_value.filter.return_value.first.side_effect = [
            mock_post,           # Post exists
            mock_existing_like   # Like already exists
        ]

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            manage_likes(
                background_tasks=self.background_tasks,
                like=like_input,
                db=self.db,
                current_user=self.current_user
            )
        
        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(context.exception.detail, "Post already liked")

    @patch('routes.likes_routes.models.Content')  # Updated patch path
    @patch('routes.likes_routes.models.Likes')    # Updated patch path
    def test_unlike_not_liked_post(self, mock_likes_model, mock_content_model):
        """Test unliking a post that hasn't been liked"""
        # Arrange
        like_input = LikeInput(post_id=1, dir=0)
        
        mock_post = Mock()
        mock_post.c_id = 1

        self.db.query.return_value.filter.return_value.first.side_effect = [
            mock_post,  # Post exists
            None        # Like doesn't exist
        ]

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            manage_likes(
                background_tasks=self.background_tasks,
                like=like_input,
                db=self.db,
                current_user=self.current_user
            )
        
        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "No like found")

if __name__ == '__main__':
    unittest.main()