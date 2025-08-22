from flask_mail import Message
from flask import current_app
import threading

def send_async_email(app, msg):
    with app.app_context():  # serve per avere il contesto Flask nel thread
        mail = current_app.extensions.get('mail')
        mail.send(msg)

def send_otp_email(email, otp):
    try:
        msg = Message(
            subject='OTP Code',
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@example.com'),
            recipients=[email],
            body=f"This is your OTP code: {otp}"
        )

        # SYNC EMAIL
        # mail = current_app.extensions.get('mail')
        # mail.send(msg)

        # Avvia un thread per mandare la mail
        thread = threading.Thread(target=send_async_email, args=(current_app._get_current_object(), msg))
        thread.start()

        return True
    except Exception as e:
        current_app.logger.error(f"Error sending email: {e}")
        return False
