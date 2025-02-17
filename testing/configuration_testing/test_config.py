import unittest
from unittest.mock import patch
from dotenv import load_dotenv
import os
from pydantic_settings import BaseSettings

# Mocked environment variables
MOCK_ENV_VARS = {
    "EMAIL_USERNAME": "test_user",
    "EMAIL_PASSWORD": "test_pass",
    "SMTP_SERVER": "smtp.example.com",
    "SMTP_PORT": "587",
    "MAIL_FROM": "noreply@example.com",
    "MAIL_TLS": "True",
    "MAIL_SSL": "False",
    "USE_CREDENTIALS": "True",
    "TWILIO_ACCOUNT_SID": "ACXXXXXXXXXXXXXXXXXX",
    "TWILIO_AUTH_TOKEN": "fake_auth_token",
    "TWILIO_PHONE_NUMBER": "+1234567890",
    "DATABASE_HOSTNAME": "localhost",
    "DATABASE_PORT": "5432",
    "DATABASE_PASSWORD": "db_password",
    "DATABASE_NAME": "test_db",
    "DATABASE_USERNAME": "db_user",
    "SECRET_KEY": "supersecret",
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRY_MINUTES": "30",
    "MAX_RETRY_ATTEMPTS": "3",
    "OTP_EXPIRATION_MINUTES": "5",
}

class TestAppSettings(unittest.TestCase):
    
    @patch.dict(os.environ, MOCK_ENV_VARS, clear=True)  # Mock environment variables for the test
    def test_settings_loading_and_database_url(self):
        """Test if AppSettings correctly loads environment variables and constructs DATABASE_URL."""
        
        # Prevent actual .env loading with this line if necessary
        # load_dotenv(dotenv_path="E:/TrendConnect/configuration/.env")  # Optional, only if needed for other vars

        class AppSettings(BaseSettings):
            EMAIL_USERNAME: str
            EMAIL_PASSWORD: str
            SMTP_SERVER: str
            SMTP_PORT: int
            MAIL_FROM: str
            MAIL_TLS: bool
            MAIL_SSL: bool
            USE_CREDENTIALS: bool
            TWILIO_ACCOUNT_SID: str
            TWILIO_AUTH_TOKEN: str
            TWILIO_PHONE_NUMBER: str
            DATABASE_HOSTNAME: str
            DATABASE_PORT: int
            DATABASE_PASSWORD: str
            DATABASE_NAME: str
            DATABASE_USERNAME: str
            SECRET_KEY: str
            ALGORITHM: str
            ACCESS_TOKEN_EXPIRY_MINUTES: int
            MAX_RETRY_ATTEMPTS: int
            OTP_EXPIRATION_MINUTES: int

        settings = AppSettings()

        # Assertions to check if values are correctly loaded
        self.assertEqual(settings.EMAIL_USERNAME, "test_user")
        self.assertEqual(settings.SMTP_SERVER, "smtp.example.com")
        self.assertEqual(settings.DATABASE_NAME, "test_db")
        self.assertEqual(settings.TWILIO_PHONE_NUMBER, "+1234567890")
        self.assertEqual(settings.ACCESS_TOKEN_EXPIRY_MINUTES, 30)

        # Construct DATABASE_URL
        DATABASE_URL = f"postgresql://{settings.DATABASE_USERNAME}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOSTNAME}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"

        # Assert that DATABASE_URL is constructed correctly
        expected_url = "postgresql://db_user:db_password@localhost:5432/test_db"
        self.assertEqual(DATABASE_URL, expected_url)

if __name__ == "__main__":
    unittest.main()
