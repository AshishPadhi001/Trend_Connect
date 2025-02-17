import unittest
from unittest.mock import patch, MagicMock, Mock
from fastapi import HTTPException, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from core import models
from routes.content_routes import get_all_content, create_content, delete_content_by_id, get_content_by_username

class TestContentRoutes(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.db = MagicMock(spec=Session)
        self.background_tasks = BackgroundTasks()
        self.current_user = models.Registration(
            user_id=1,
            username="test_user"
        )
        
        # Mock content data
        self.mock_content = models.Content(
            c_id=1,
            user_id=1,
            username="test_user",
            title="Test Title",
            caption="Test Caption",
            created_at=datetime.now(),
            file="test_file.jpg"
        )

    def mock_db_content(self, count=6):
        """Helper to create mock content list"""
        return [
            models.Content(
                c_id=i,
                user_id=1,
                username="test_user",
                title=f"Test Title {i}",
                caption=f"Test Caption {i}",
                created_at=datetime.now(),
                file=f"test_file_{i}.jpg"
            ) for i in range(1, count + 1)
        ]

    @patch("tasks.savecontent.save_content_to_folder_background")
    @patch("tasks.notify_followers.notify_followers_background")
    async def test_create_content_success(self, mock_notify, mock_save):
        """Test successful content creation."""
        # Arrange
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        
        mock_save.return_value = {
            "username": "test_user",
            "title": "Test Title",
            "caption": "Test Caption",
            "created_at": datetime.now(),
            "file": "test.jpg"
        }

        # Act
        response = await create_content(
            background_tasks=self.background_tasks,
            username="test_user",
            title="Test Title",
            caption="Test Caption",
            file=mock_file,
            db=self.db,
            current_user=self.current_user
        )

        # Assert
        self.assertIn("message", response)
        self.assertIn("content_id", response)
        self.assertEqual(response["message"], "Content created successfully")
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()

    def test_get_all_content_success(self):
        """Test successful retrieval of all content with pagination."""
        # Arrange
        mock_contents = self.mock_db_content()
        self.db.query().count.return_value = len(mock_contents)
        self.db.query().offset().limit().all.return_value = mock_contents
        
        # Mock likes and comments
        self.db.query(models.Likes).filter().count.return_value = 5
        self.db.query(models.Comment).filter().all.return_value = []

        # Act
        response = get_all_content(page=1, db=self.db, current_user=self.current_user)

        # Assert
        self.assertIn("content", response)
        self.assertIn("total_content", response)
        self.assertIn("total_pages", response)
        self.assertIn("current_page", response)
        self.assertEqual(response["current_page"], 1)
        self.assertEqual(len(response["content"]), 6)

    def test_get_all_content_invalid_page(self):
        """Test getting content with invalid page number."""
        # Arrange
        self.db.query().count.return_value = 6
        
        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            get_all_content(page=2, db=self.db, current_user=self.current_user)
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Invalid choice of page")

    def test_get_content_by_username_success(self):
        """Test successful retrieval of content by username."""
        # Arrange
        mock_contents = self.mock_db_content(3)
        self.db.query().filter().count.return_value = len(mock_contents)
        self.db.query().filter().offset().limit().all.return_value = mock_contents
        
        # Mock likes and comments
        self.db.query(models.Likes).filter().count.return_value = 5
        self.db.query(models.Comment).filter().all.return_value = []

        # Act
        response = get_content_by_username(
            username="test_user",
            page=1,
            db=self.db,
            current_user=self.current_user
        )

        # Assert
        self.assertIn("content", response)
        self.assertEqual(len(response["content"]), 3)
        self.assertEqual(response["current_page"], 1)

    @patch("tasks.deletecontent.delete_content_folder_background")
    def test_delete_content_success(self, mock_delete):
        """Test successful content deletion."""
        # Arrange
        self.db.query().filter().first.return_value = self.mock_content

        # Act
        response = delete_content_by_id(
            id=1,
            db=self.db,
            current_user=self.current_user,
            background_tasks=self.background_tasks
        )

        # Assert
        self.assertEqual(response["message"], "Content deleted successfully")
        self.assertEqual(response["id"], 1)
        self.db.delete.assert_called_once()
        self.db.commit.assert_called_once()
        self.assertEqual(len(self.background_tasks.tasks), 1)

    def test_delete_content_not_found(self):
        """Test deletion of non-existent content."""
        # Arrange
        self.db.query().filter().first.return_value = None

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            delete_content_by_id(
                id=999,
                db=self.db,
                current_user=self.current_user,
                background_tasks=self.background_tasks
            )

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "No content found with ID 999")

    def test_delete_content_unauthorized(self):
        """Test deletion by unauthorized user."""
        # Arrange
        self.mock_content.username = "other_user"
        self.db.query().filter().first.return_value = self.mock_content

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            delete_content_by_id(
                id=1,
                db=self.db,
                current_user=self.current_user,
                background_tasks=self.background_tasks
            )

        self.assertEqual(context.exception.status_code, 403)
        self.assertEqual(context.exception.detail, "Not authorized to delete this content")

if __name__ == '__main__':
    unittest.main()