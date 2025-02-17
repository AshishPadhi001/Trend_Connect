from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from core import models
from configuration.config import settings  # Import settings from the config file

# Function to send an email
def send_email_notification(to_email: str, title: str, caption: str, username: str):
    try:
        sender_email = settings.EMAIL_USERNAME
        sender_password = settings.EMAIL_PASSWORD
        smtp_server = settings.SMTP_SERVER
        smtp_port = settings.SMTP_PORT
        mail_from = settings.MAIL_FROM

        subject = f"New Post from {username}: {title}"
        body = f"Hi,\n\n{username} has posted new content:\n\nTitle: {title}\nCaption: {caption}\n\nCheck it out!"

        msg = MIMEMultipart()
        msg["From"] = mail_from
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Send email using TLS (since SSL on port 587 is incorrect)
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())

        print(f"Email sent to {to_email}")

    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")

# Background task to notify followers
def notify_followers_background(username: str, title: str, caption: str, db: Session, background_tasks: BackgroundTasks):
    user = db.query(models.Registration).filter(models.Registration.username == username).first()
    
    if user:
        followers = db.query(models.Follows).filter(models.Follows.following_id == user.user_id).all()
        follower_emails = [follower.follower.email for follower in followers]

        for email in follower_emails:
            background_tasks.add_task(send_email_notification, email, title, caption, username)
