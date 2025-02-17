
from fastapi import BackgroundTasks
from utils.email_service import send_email
from utils.sms_service import send_sms

async def send_otp_background(email: str,otp: str):
    await send_email(
        email=email,
        subject="Your OTP for Registration",
        template_name="styles.html",
        context={"otp": otp}
    )
    #await send_sms(phone_number, otp)