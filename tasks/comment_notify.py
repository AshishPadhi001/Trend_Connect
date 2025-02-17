from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from core.database import get_db
from core import models
from oauth2 import get_current_user
from schemas.comments import CommentInput
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from configuration.config import settings  # Import settings from your config file

# Function to send an email notification in the background
def send_comment_notification(to_email: str, post_title: str, comment_text: str, commenter_username: str):
    try:
        sender_email = settings.EMAIL_USERNAME
        sender_password = settings.EMAIL_PASSWORD
        smtp_server = settings.SMTP_SERVER
        smtp_port = settings.SMTP_PORT
        mail_from = settings.MAIL_FROM

        sender_name = "Trend Connect"
        from_address = f"{sender_name} <{mail_from}>"

        subject = "Trend Connect Notifications: Someone commented on your post!"
        body = f"Hi,\n\n{commenter_username} has commented on your post!\n\nTitle: {post_title}\nComment: {comment_text}\n\nCheck it out!"

        msg = MIMEMultipart()
        msg["From"] = from_address
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


# Background task to notify post owner about the comment
def notify_post_owner_background(post_id: int, comment_text: str, commenter_username: str, db: Session, background_tasks: BackgroundTasks):
    # Fetch the post details
    post = db.query(models.Content).filter(models.Content.c_id == post_id).first()
    
    if post:
        # Get the post owner's email
        post_owner = db.query(models.Registration).filter(models.Registration.user_id == post.user_id).first()
        
        if post_owner:
            # Send the email notification in the background
            background_tasks.add_task(
                send_comment_notification, 
                post_owner.email, 
                post.title, 
                comment_text, 
                commenter_username
            )