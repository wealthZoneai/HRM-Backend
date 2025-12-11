import secrets
from django.core.mail import send_mail
from django.conf import settings


def generate_otp():
    return f"{secrets.randbelow(10**6):06d}"


def send_otp_email(email, otp):
    subject = "Password Reset OTP - HRMS Portal"
    message = f"Your OTP to reset password is: {otp}\nValid for 10 minutes."

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
