##Registration.py

from pydantic import BaseModel, EmailStr
from datetime import date

class RegisterUser(BaseModel):
    email: EmailStr

class VerifyOTP(BaseModel):
    email: EmailStr
    otp: int

class RegisterUserDetails(BaseModel):
    email: EmailStr
    username: str
    password: str
    phone_number: str
    country: str
    dob: date


class RegistrationResponse(BaseModel):
    user_id: int
    username: str

    class Config:
        from_attributes = True

