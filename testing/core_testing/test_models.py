import unittest
from unittest.mock import patch, MagicMock
from core.models import Registration, Content, Likes, Comment, Follows

class TestDatabaseModels(unittest.TestCase):

    @patch('core.database.SessionLocal')  # Correct path for SessionLocal
    def test_create_registration(self, mock_session_local):
        # Create a mock session
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        # Create a new Registration instance
        new_user = Registration(
            username="testuser",
            password="testpassword",
            email="test@example.com",
            dob="1990-01-01",
            phone_number="1234567890",
            country="TestCountry",
            is_active=True
        )

        # Add the new user to the mock session
        mock_session.add(new_user)
        mock_session.commit()

        # Test that session.add and session.commit were called
        mock_session.add.assert_called_once_with(new_user)
        mock_session.commit.assert_called_once()

    @patch('core.database.SessionLocal')  # Correct path for SessionLocal
    def test_create_content(self, mock_session_local):
        # Create a mock session
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        # Mock the user that the content will belong to
        mock_user = MagicMock(spec=Registration)
        mock_user.user_id = 1
        new_content = Content(
            user_id=mock_user.user_id,
            username=mock_user.username,
            title="Test Title",
            caption="Test Caption",
            file="test_file.txt"
        )

        # Add the new content to the mock session
        mock_session.add(new_content)
        mock_session.commit()

        # Test that session.add and session.commit were called
        mock_session.add.assert_called_once_with(new_content)
        mock_session.commit.assert_called_once()

    @patch('core.database.SessionLocal')  # Correct path for SessionLocal
    def test_create_like(self, mock_session_local):
        # Create a mock session
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        # Create a mock like object
        mock_like = Likes(
            user_id=1,
            post_id=1
        )

        # Add the new like to the mock session
        mock_session.add(mock_like)
        mock_session.commit()

        # Test that session.add and session.commit were called
        mock_session.add.assert_called_once_with(mock_like)
        mock_session.commit.assert_called_once()

    @patch('core.database.SessionLocal')  # Correct path for SessionLocal
    def test_create_comment(self, mock_session_local):
        # Create a mock session
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        # Create a mock comment object
        mock_comment = Comment(
            user_id=1,
            post_id=1,
            user_comment="This is a comment."
        )

        # Add the new comment to the mock session
        mock_session.add(mock_comment)
        mock_session.commit()

        # Test that session.add and session.commit were called
        mock_session.add.assert_called_once_with(mock_comment)
        mock_session.commit.assert_called_once()

    @patch('core.database.SessionLocal')  # Correct path for SessionLocal
    def test_create_follow(self, mock_session_local):
        # Create a mock session
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        # Create a mock follow object
        mock_follow = Follows(
            follower_id=1,
            following_id=2
        )

        # Add the new follow to the mock session
        mock_session.add(mock_follow)
        mock_session.commit()

        # Test that session.add and session.commit were called
        mock_session.add.assert_called_once_with(mock_follow)
        mock_session.commit.assert_called_once()

if __name__ == '__main__':
    unittest.main()
