from utils.email_service import send_email

#Background task fro sending email when updated details by user 
async def send_update_email_background(email: str, username: str):
    update_email_context = {
        "username": username,
    }
    try:
        await send_email(
            email,
            "Account Updated - Trend Connect",
            "userupdate.html",
            update_email_context
        )
    except Exception as e:
        print(f"Background task - Error sending update email: {e}")