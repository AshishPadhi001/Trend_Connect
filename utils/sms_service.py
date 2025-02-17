from fastapi import HTTPException
from twilio.rest import Client
from configuration.config import settings
import asyncio  # For async functionality
from twilio.base.exceptions import TwilioRestException  # For specific Twilio error handling


#Send sms 
async def send_sms(phone_number: str, otp: str):
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"""Trend Connect - Your registration code is:
📱 {otp}

Please use it within the next {settings.OTP_EXPIRATION_MINUTES} minutes.
If you didn't request this, please ignore this message.""",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        return True
    except TwilioRestException as twilio_error:
        # Handle specific Twilio errors
        raise HTTPException(
            status_code=500, 
            detail=f"Twilio error: {str(twilio_error)}"
        )
    except Exception as e:
        # Handle any other unexpected errors
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to send SMS: {str(e)}"
        )