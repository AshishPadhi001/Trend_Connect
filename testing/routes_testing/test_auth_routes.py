import unittest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from routes.auth_routes import router
from core.models import Registration
from utils.hashing import verify
from oauth2 import create_tokens
from unittest.mock import patch, MagicMock

class TestAuthRoutes(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize test client once for all test cases"""
        app = FastAPI()
        app.include_router(router)
        cls.client = TestClient(app)

    @patch("core.database.get_db")
    def test_login_success(self, mock_get_db):
        """Test successful login"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_user = Registration(username="testuser", password="hashedpassword", user_id=10)
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        mock_token_response = {
            "access_token": "mock_access_token",
            "token_type": "bearer"
        }

        with patch("routes.auth_routes.verify", return_value=True) as mock_verify, \
             patch("routes.auth_routes.create_tokens", return_value=mock_token_response) as mock_tokens:

            response = self.client.post(
                "/login",
                data={"username": "testuser", "password": "password"},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            self.assertTrue(mock_verify.called)
            self.assertTrue(mock_tokens.called)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {
                "message": "Login successful",
                "token": mock_token_response,
                "token_type": "bearer",
                "user_id": 10
            })

    @patch("core.database.get_db")
    def test_login_user_not_found(self, mock_get_db):
        """Test login when user does not exist"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = self.client.post("/login", data={"username": "unknown", "password": "password"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "No user found with username unknown. Go and register yourself first"})

    @patch("core.database.get_db")
    def test_login_wrong_password(self, mock_get_db):
        """Test login with incorrect password"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_user = Registration(username="testuser", password="hashedpassword", user_id=1)

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with patch("routes.auth_routes.verify", return_value=False) as mock_verify:
            response = self.client.post(
                "/login",
                data={"username": "testuser", "password": "wrongpassword"},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            self.assertTrue(mock_verify.called)
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.json(), {"detail": "Incorrect password"})

    def test_login_welcome(self):
        """Test login welcome message"""
        response = self.client.get("/login_welcome")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Welcome to Login Section of Trend Connect"})

    def test_logout(self):
        """Test logout functionality"""
        response = self.client.post("/logout")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "message": "You have been logged out. Please remove the token from your client-side storage."
        })

if __name__ == "__main__":
    unittest.main()