import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

def send_email(to_email, subject, body):
    smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.example.com')
    smtp_port = current_app.config.get('SMTP_PORT', 587)
    smtp_user = current_app.config.get('SMTP_USER', 'noreply@example.com')
    smtp_password = current_app.config.get('SMTP_PASSWORD', '')
    from_email = smtp_user

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        current_app.logger.error(f"Email send error: {str(e)}")
        return False
from flask import current_app
from flask_mail import Message
from extensions import mail
import logging

logger = logging.getLogger(__name__)

def send_verification_email(email, verification_code):
    try:
        # Log email configuration for debugging
        logger.debug(f"Mail Server: {current_app.config['MAIL_SERVER']}")
        logger.debug(f"Mail Port: {current_app.config['MAIL_PORT']}")
        logger.debug(f"Mail Use TLS: {current_app.config['MAIL_USE_TLS']}")
        
        msg = Message('Verify your SammyA account',
                     sender=current_app.config['MAIL_DEFAULT_SENDER'],
                     recipients=[email])
        
        msg.body = f"""
        Welcome to SammyA!
        Your verification code is: {verification_code}
        This code will expire in 10 minutes.
        """
        
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #1a56db;">Welcome to SammyA!</h2>
            <p>Your verification code is:</p>
            <div style="background-color: #f3f4f6; padding: 20px; text-align: center; 
                        font-size: 24px; letter-spacing: 5px; margin: 20px 0;">
                <strong>{verification_code}</strong>
            </div>
        </div>
        """
        
        # Add debug logging before sending
        logger.debug(f"Attempting to send email to {email}")
        mail.send(msg)
        logger.info(f"Successfully sent verification email to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}", exc_info=True)
        raise