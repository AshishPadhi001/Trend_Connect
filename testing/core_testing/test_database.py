import unittest  # Importing the unittest module to write unit tests
from unittest.mock import patch, MagicMock  # Import patching tools to mock components
from core.database import get_db  # Import the function to test (get_db)

class TestDatabase(unittest.TestCase):  # Define the test class inheriting from unittest.TestCase
    @patch('core.database.SessionLocal')  # Patching SessionLocal so we can mock it during the test
    def test_get_db(self, mock_session_local):  # Test method for checking the database connection
        mock_session = MagicMock()  # Create a mock object to simulate the session
        
        mock_session_local.return_value = mock_session  # Mock the return value of SessionLocal to be the mock session
        
        db_generator = get_db()  # Call the get_db function, which should yield a session
        db_instance = next(db_generator)  # Get the session instance from the generator
        
        # Check if SessionLocal was called exactly once to create a session
        mock_session_local.assert_called_once()
        
        # Ensure that the yielded instance is the mock session (i.e., it was returned from the generator)
        self.assertEqual(db_instance, mock_session)
        
        db_generator.close()  # Simulate closing the generator (this calls db.close() in the finally block)
        
        # Verify that the mock session's close method was called exactly once
        mock_session.close.assert_called_once()

if __name__ == '__main__':  # If this file is run directly (not imported), start the tests
    unittest.main()
