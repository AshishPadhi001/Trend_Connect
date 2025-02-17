import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.models import Registration, Content
from routes.search_routes import search_users, search_content_by_title

class TestSearchRoutes(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        self.db = Mock(spec=Session)
        self.current_user = Mock()
        self.current_user.user_id = 1
        self.current_user.username = "testuser"

        # Create sample users for testing
        self.mock_users = [
            Mock(spec=Registration, username="test1"),
            Mock(spec=Registration, username="test2"),
            Mock(spec=Registration, username="tester"),
            Mock(spec=Registration, username="testing"),
            Mock(spec=Registration, username="testpro"),
            Mock(spec=Registration, username="testmax"),
            Mock(spec=Registration, username="testhero")
        ]

        # Create sample content for testing
        self.mock_content = [
            Mock(spec=Content, c_id=1, title="First Post", username="user1", 
                 created_at=datetime(2024, 1, 1)),
            Mock(spec=Content, c_id=2, title="Second Post", username="user2", 
                 created_at=datetime(2024, 1, 2)),
            Mock(spec=Content, c_id=3, title="Third Post", username="user3", 
                 created_at=datetime(2024, 1, 3)),
            Mock(spec=Content, c_id=4, title="Fourth Post", username="user4", 
                 created_at=datetime(2024, 1, 4)),
            Mock(spec=Content, c_id=5, title="Fifth Post", username="user5", 
                 created_at=datetime(2024, 1, 5)),
            Mock(spec=Content, c_id=6, title="Sixth Post", username="user6", 
                 created_at=datetime(2024, 1, 6)),
            Mock(spec=Content, c_id=7, title="Seventh Post", username="user7", 
                 created_at=datetime(2024, 1, 7))
        ]

    def test_search_users_success_first_page(self):
        """Test successful user search with first page results"""
        # Arrange
        self.db.query.return_value.filter.return_value.all.return_value = self.mock_users

        # Act
        result = search_users(
            username="test",
            page=1,
            db=self.db,
            current_user=self.current_user
        )

        # Assert
        self.assertEqual(result["total_users"], 7)
        self.assertEqual(result["total_pages"], 2)
        self.assertEqual(result["current_page"], 1)
        self.assertEqual(len(result["users"]), 6)  # PAGE_SIZE is 6

    def test_search_users_success_second_page(self):
        """Test successful user search with second page results"""
        # Arrange
        self.db.query.return_value.filter.return_value.all.return_value = self.mock_users

        # Act
        result = search_users(
            username="test",
            page=2,
            db=self.db,
            current_user=self.current_user
        )

        # Assert
        self.assertEqual(result["current_page"], 2)
        self.assertEqual(len(result["users"]), 1)  # Last remaining user

    def test_search_users_invalid_page(self):
        """Test user search with invalid page number"""
        # Arrange
        self.db.query.return_value.filter.return_value.all.return_value = self.mock_users

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            search_users(
                username="test",
                page=3,  # More than total pages
                db=self.db,
                current_user=self.current_user
            )
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Invalid choice of page")

    def test_search_users_no_results(self):
        """Test user search with no matching results"""
        # Arrange
        self.db.query.return_value.filter.return_value.all.return_value = []

        # Act
        result = search_users(
            username="nonexistent",
            page=1,
            db=self.db,
            current_user=self.current_user
        )

        # Assert
        self.assertEqual(result["total_users"], 0)
        self.assertEqual(result["total_pages"], 0)
        self.assertEqual(len(result["users"]), 0)

    def test_search_content_by_title_success(self):
        """Test successful content search by title"""
        # Arrange
        self.db.query.return_value.filter.return_value.all.return_value = self.mock_content

        # Act
        result = search_content_by_title(
            title="Post",
            page=1,
            db=self.db,
            current_user=self.current_user
        )

        # Assert
        self.assertEqual(result["total_content"], 7)
        self.assertEqual(result["total_pages"], 2)
        self.assertEqual(len(result["content"]), 6)  # PAGE_SIZE is 6

    def test_search_content_by_id(self):
        """Test content search by ID"""
        # Arrange
        mock_single_content = [self.mock_content[0]]  # Just the first content
        self.db.query.return_value.filter.return_value.all.return_value = mock_single_content

        # Act
        result = search_content_by_title(
            title="1",  # Search by ID
            page=1,
            db=self.db,
            current_user=self.current_user
        )

        # Assert
        self.assertEqual(result["total_content"], 1)
        self.assertEqual(result["total_pages"], 1)
        self.assertEqual(len(result["content"]), 1)
        self.assertEqual(result["content"][0]["title"], "First Post")

    def test_search_content_invalid_page(self):
        """Test content search with invalid page number"""
        # Arrange
        self.db.query.return_value.filter.return_value.all.return_value = self.mock_content

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            search_content_by_title(
                title="Post",
                page=3,  # More than total pages
                db=self.db,
                current_user=self.current_user
            )
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Invalid choice of page")

    def test_search_content_no_results(self):
        """Test content search with no matching results"""
        # Arrange
        self.db.query.return_value.filter.return_value.all.return_value = []

        # Act
        result = search_content_by_title(
            title="nonexistent",
            page=1,
            db=self.db,
            current_user=self.current_user
        )

        # Assert
        self.assertEqual(result["total_content"], 0)
        self.assertEqual(result["total_pages"], 0)
        self.assertEqual(len(result["content"]), 0)

    def test_search_content_date_formatting(self):
        """Test that content search results include properly formatted dates"""
        # Arrange
        mock_single_content = [self.mock_content[0]]
        self.db.query.return_value.filter.return_value.all.return_value = mock_single_content

        # Act
        result = search_content_by_title(
            title="First",
            page=1,
            db=self.db,
            current_user=self.current_user
        )

        # Assert
        self.assertEqual(result["content"][0]["created_at"], datetime(2024, 1, 1))

if __name__ == '__main__':
    unittest.main()