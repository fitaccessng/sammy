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