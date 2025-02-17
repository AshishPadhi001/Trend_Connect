import unittest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta, date
from fastapi import HTTPException
import asyncio
from routes.user_routes import (
    send_otp,
    verify_otp,
    complete_registration,
    get_all_users,
    get_user_by_id,
    update_user,
    delete_user
)
from schemas.registration import RegisterUser, VerifyOTP, RegistrationResponse, RegisterUserDetails

class TestUserRoutes(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        self.mock_db = Mock()
        self.mock_background_tasks = Mock()
        
        # Common test data with proper date format
        self.valid_email = "test@example.com"
        self.valid_otp = "123456"
        self.valid_user_data = {
            "email": self.valid_email,
            "username": "testuser",
            "password": "StrongP@ssw0rd123",
            "phone_number": "1234567890",
            "country": "USA",
            "dob": date(2000, 1, 1)  # Using date object instead of string
        }
        
        # Set up async event loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    async def async_test_send_otp_new_user(self):
        """Test sending OTP to a new user"""
        with patch('routes.user_routes.generate_otp', return_value=self.valid_otp):
            self.mock_db.query.return_value.filter.return_value.first.return_value = None
            
            # Create RegisterUser instance
            user_data = {"email": self.valid_email}
            user = RegisterUser(**user_data)
            
            result = await send_otp(
                user=user,
                background_tasks=self.mock_background_tasks,
                db=self.mock_db
            )
            
            self.assertIn("OTP sent successfully", result["message"])
            self.mock_db.add.assert_called_once()
            self.mock_background_tasks.add_task.assert_called_once()

    def test_send_otp_new_user(self):
        self.loop.run_until_complete(self.async_test_send_otp_new_user())

    async def async_test_send_otp_existing_active_user(self):
        """Test sending OTP to an already active user"""
        mock_existing_user = Mock(
            email=self.valid_email,
            is_active=True
        )
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_existing_user
        
        user_data = {"email": self.valid_email}
        user = RegisterUser(**user_data)
        
        with self.assertRaises(HTTPException) as context:
            await send_otp(
                user=user,
                background_tasks=self.mock_background_tasks,
                db=self.mock_db
            )
        
        self.assertEqual(context.exception.status_code, 226)
        self.assertIn("already registered", str(context.exception.detail))

    def test_send_otp_existing_active_user(self):
        self.loop.run_until_complete(self.async_test_send_otp_existing_active_user())

    def test_verify_otp_success(self):
        """Test successful OTP verification"""
        # Mock user with matching OTP
        mock_user = Mock(
            otp=self.valid_otp,
            otp_expiry=datetime.utcnow() + timedelta(minutes=10)
        )
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        verify_data = {"email": self.valid_email, "otp": self.valid_otp}
        verify_otp_data = VerifyOTP(**verify_data)
        
        # Mock the OTP comparison
        mock_user.otp = self.valid_otp
        
        result = verify_otp(data=verify_otp_data, db=self.mock_db)
        self.assertIn("OTP verified successfully", result["message"])

    async def async_test_complete_registration_success(self):
        """Test successful user registration completion"""
        with patch('routes.user_routes.age_difference', return_value=(20, 0, 0, 0, 0)), \
             patch('routes.user_routes.check_password_strength', return_value="high"), \
             patch('routes.user_routes.validate_phone_number', return_value=True), \
             patch('routes.user_routes.hashing', return_value="hashed_password"):
            
            mock_user = Mock(
                email=self.valid_email,
                is_active=False,
                user_id=1,
                username="testuser"
            )
            self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
            
            user_details = RegisterUserDetails(**self.valid_user_data)
            
            result = await complete_registration(
                user_details=user_details,
                background_tasks=self.mock_background_tasks,
                db=self.mock_db
            )
            
            self.assertEqual(result.user_id, 1)
            self.assertEqual(result.username, "testuser")
            self.assertTrue(mock_user.is_active)
            self.mock_db.commit.assert_called_once()

    def test_complete_registration_success(self):
        self.loop.run_until_complete(self.async_test_complete_registration_success())

    async def async_test_update_user_success(self):
        """Test successful user update"""
        with patch('routes.user_routes.hashing', return_value="hashed_password"):
            mock_current_user = Mock(username="testuser")
            
            mock_user = Mock(
                username="testuser",
                email=self.valid_email,
                user_id=1
            )
            self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
            
            # Create updated user data with all required fields
            updated_user_data = {
                "email": "newemail@example.com",
                "username": "newusername",
                "password": "NewStrongP@ss123",
                "phone_number": "9876543210",
                "country": "Canada",
                "dob": date(2000, 1, 1)
            }
            updated_user = RegisterUserDetails(**updated_user_data)
            
            result = await update_user(
                background_tasks=self.mock_background_tasks,
                user_id=1,
                updated_user=updated_user,
                db=self.mock_db,
                current_user=mock_current_user
            )
            
            self.mock_db.commit.assert_called_once()
            self.mock_db.refresh.assert_called_once_with(mock_user)
            self.mock_background_tasks.add_task.assert_called_once()

    def test_update_user_success(self):
        self.loop.run_until_complete(self.async_test_update_user_success())

    async def async_test_delete_user_success(self):
        """Test successful user deletion"""
        mock_current_user = Mock(username="testuser")
        mock_user = Mock(
            username="testuser",
            email=self.valid_email
        )
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        await delete_user(
            user_id=1,
            background_tasks=self.mock_background_tasks,
            db=self.mock_db,
            current_user=mock_current_user
        )
        
        self.mock_db.delete.assert_called_once_with(mock_user)
        self.mock_db.commit.assert_called_once()
        self.mock_background_tasks.add_task.assert_called_once()

    def test_delete_user_success(self):
        self.loop.run_until_complete(self.async_test_delete_user_success())

if __name__ == '__main__':
    unittest.main()