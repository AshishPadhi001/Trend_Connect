from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from core import models
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from configuration.config import settings  # Import settings from your config file
from core.database import get_db

# Function to send an email notification
def send_email_notification(to_email: str, post_title: str, post_caption: str, current_user_username: str):
    try:
        sender_email = settings.EMAIL_USERNAME
        sender_password = settings.EMAIL_PASSWORD
        smtp_server = settings.SMTP_SERVER
        smtp_port = settings.SMTP_PORT
        mail_from = settings.MAIL_FROM

        # Set the sender to "Trend Connect" and include the email address
        sender_name = "Trend Connect"
        from_address = f"{sender_name} <{mail_from}>"

        subject = "Trend Connect Notifications: Someone liked your post!"
        body = f"Hi,\n\n{current_user_username} has liked your post!\n\nTitle: {post_title}\nCaption: {post_caption}\n\nCheck it out!"

        msg = MIMEMultipart()
        msg["From"] = from_address  # Use "Trend Connect" as the sender
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Send email using TLS
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())

        print(f"Email sent to {to_email}")

    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")


# Background task to notify post owner about the like
def notify_post_owner_background(post_id: int, db: Session, current_user_username: str):
    # Fetch the post details
    post = db.query(models.Content).filter(models.Content.c_id == post_id).first()
    
    if post:
        # Get the post owner's email
        post_owner = db.query(models.Registration).filter(models.Registration.user_id == post.user_id).first()
        
        if post_owner:
            # Send the email notification in the background
            send_email_notification(
                post_owner.email, 
                post.title, 
                post.caption, 
                current_user_username  # Send the username directly from function argument
            )
