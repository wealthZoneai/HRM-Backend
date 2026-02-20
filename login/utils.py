import secrets
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def generate_otp():
    # Secure random 6-digit OTP
    return f"{secrets.randbelow(10**6):06d}"


def send_otp_email(email, otp):
    subject = "Password Reset OTP - HRMS Portal"
    message = f"Your OTP is {otp}. It is valid for 5 minutes."

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
