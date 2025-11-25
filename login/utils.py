import random
from django.core.mail import send_mail
from django.conf import settings

def generate_otp():
    return str(random.randint(1000, 9999))  # 4-digit OTP

def send_otp_email(email, otp):
    subject = "Password Reset OTP - HRMS Portal"
    message = f"Your OTP to reset password is: {otp}\nValid for 10 minutes."
    
    # For now, console/email backend for development
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,  
        [email],
        fail_silently=False,
    )
