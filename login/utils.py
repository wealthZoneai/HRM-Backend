import secrets
from django.core.mail import send_mail
from django.conf import settings
import logging
logger = logging.getLogger(__name__)


def generate_otp():
    return f"{secrets.randbelow(10**6):06d}"


def send_otp_email(email, otp):
    subject = "Password Reset OTP - HRMS Portal"
    message = f"Your OTP to reset password is: {otp}\nValid for 10 minutes."
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
    except Exception as e:
        logger.exception("Failed to send OTP email to %s", email)
        # consider raising a custom error or returning False so caller can respond gracefully
        raise