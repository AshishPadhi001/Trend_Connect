from jinja2 import Environment, FileSystemLoader
from fastapi_mail import MessageSchema, FastMail
from fastapi_mail.config import ConnectionConfig
from fastapi import HTTPException
from configuration.config import settings

# Set up email configuration
mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.EMAIL_USERNAME,
    MAIL_PASSWORD=settings.EMAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_SERVER,
    MAIL_FROM_NAME="Trend Connect",
    MAIL_STARTTLS=settings.MAIL_TLS,
    MAIL_SSL_TLS=settings.MAIL_SSL,
    USE_CREDENTIALS=settings.USE_CREDENTIALS
)

# Jinja2 Template Environment Setup
template_env = Environment(
    loader=FileSystemLoader('E:\\TrendConnect\\templates'),  # Corrected file path
    autoescape=True
)

async def send_email(email: str, subject: str, template_name: str, context: dict):
    try: 
        # Render the template with context data
        template = template_env.get_template(template_name)
        html_body = template.render(context)
        
        
        # Send email using FastMail
        message = MessageSchema(
            subject=subject,
            recipients=[email],
            body=html_body,
            subtype="html",
        )
        fm = FastMail(mail_config)
        await fm.send_message(message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending email: {e}")
