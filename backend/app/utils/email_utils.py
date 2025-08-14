from flask_mail import Message
from flask import current_app

def send_otp_email(email, otp):
    """Invia l'OTP via email."""
    try:
        msg = Message(
            subject='OTP Code',
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@example.com'),
            recipients=[email],
            body=f"This is your OTP code: {otp}"
        )
        mail = current_app.extensions.get('mail')
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Error sending email: {e}")
        return False
