import unittest
from unittest.mock import patch, MagicMock
from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from core import models
from schemas.comments import CommentInput
from routes.comments_routes import add_comment
from tasks.comment_notify import notify_post_owner_background

class TestCommentRoutes(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.db = MagicMock(spec=Session)
        self.background_tasks = BackgroundTasks()
        self.current_user = models.Registration(
            user_id=1,
            username="test_user"
        )
        
        # Common test data
        self.valid_comment_input = CommentInput(
            post_id=1,
            user_comment="Test comment"
        )
        self.mock_post = models.Content(
            c_id=1,
            title="Test Post",
            caption="Test Caption"
        )
        self.mock_comment = models.Comment(
            comment_id=1,
            user_id=self.current_user.user_id,
            post_id=self.valid_comment_input.post_id,
            user_comment=self.valid_comment_input.user_comment
        )

    def mock_db_success_scenario(self):
        """Helper method to set up successful database operation mocks."""
        self.db.query.return_value.filter.return_value.first.return_value = self.mock_post
        self.db.add.return_value = None
        self.db.commit.return_value = None
        self.db.refresh.side_effect = lambda x: setattr(x, "comment_id", 1)

    # Fix: Updated the patch path to target the correct module
    @patch("tasks.comment_notify.notify_post_owner_background")
    def test_add_comment_success(self, mock_notify):
        """Test successful comment creation with all valid inputs."""
        # Arrange
        self.mock_db_success_scenario()

        # Act
        response = add_comment(
            self.valid_comment_input,
            self.background_tasks,
            self.db,
            self.current_user
        )

        # Assert
        self.assertEqual(response["message"], "Comment added successfully")
        self.assertEqual(response["comment"]["user_id"], self.current_user.user_id)
        self.assertEqual(response["comment"]["post_id"], self.valid_comment_input.post_id)
        self.assertEqual(response["comment"]["user_comment"], self.valid_comment_input.user_comment)
        self.assertEqual(response["comment"]["comment_id"], 1)

        # Verify database operations
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()

        # Verify background task was added
        self.assertEqual(len(self.background_tasks.tasks), 1)

    def test_add_comment_post_not_found(self):
        """Test comment creation when post doesn't exist."""
        # Arrange
        self.db.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            add_comment(
                self.valid_comment_input,
                self.background_tasks,
                self.db,
                self.current_user
            )

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "Post not found")
        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()

    @patch("tasks.comment_notify.notify_post_owner_background")
    def test_add_comment_database_error(self, mock_notify):
        """Test handling of database errors during comment creation."""
        # Arrange
        self.mock_db_success_scenario()
        self.db.commit.side_effect = Exception("Database error")

        # Act & Assert
        with self.assertRaises(Exception) as context:
            add_comment(
                self.valid_comment_input,
                self.background_tasks,
                self.db,
                self.current_user
            )

        self.assertEqual(str(context.exception), "Database error")
        self.assertEqual(len(self.background_tasks.tasks), 0)

    @patch("tasks.comment_notify.notify_post_owner_background")
    def test_add_comment_with_long_comment(self, mock_notify):
        """Test adding a comment with maximum length."""
        # Arrange
        long_comment = "x" * 1000
        comment_input = CommentInput(
            post_id=1,
            user_comment=long_comment
        )
        self.mock_db_success_scenario()

        # Act
        response = add_comment(
            comment_input,
            self.background_tasks,
            self.db,
            self.current_user
        )

        # Assert
        self.assertEqual(response["message"], "Comment added successfully")
        self.assertEqual(response["comment"]["user_comment"], long_comment)
        self.assertEqual(len(self.background_tasks.tasks), 1)

    # Fix: Updated test to verify background tasks directly instead of mock
    def test_background_task_registration(self):
        """Test that background task is properly registered."""
        # Arrange
        self.mock_db_success_scenario()
        
        # Act
        add_comment(
            self.valid_comment_input,
            self.background_tasks,
            self.db,
            self.current_user
        )

        # Assert
        self.assertEqual(len(self.background_tasks.tasks), 1)

if __name__ == '__main__':
    unittest.main()