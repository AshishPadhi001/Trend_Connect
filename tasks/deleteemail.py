from utils.email_service import send_email

#Send email when user gets deleted
async def send_deletion_email_background(email: str, username: str):
    deletion_email_context = {
        "username": username,
    }
    try:
        await send_email(
            email,
            "Account Deleted - Trend Connect",
            "userdelete.html",
            deletion_email_context
        )
    except Exception as e:
        print(f"Background task - Error sending deletion email: {e}")