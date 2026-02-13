from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
import datetime


class User(AbstractUser):
    # Single source of truth for roles
    ROLE_MANAGEMENT = "management"
    ROLE_DM = "delivery_manager"
    ROLE_PM = "project_manager"
    ROLE_HR = "hr"
    ROLE_TL = "tl"
    ROLE_EMPLOYEE = "employee"
    ROLE_INTERN = "intern"
    ROLE_IT = "it"

    ROLE_CHOICES = [
        (ROLE_MANAGEMENT, "Management"),
        (ROLE_DM, "Delivery Manager"),
        (ROLE_PM, "Project Manager"),
        (ROLE_HR, "HR"),
        (ROLE_TL, "Team Leader"),
        (ROLE_EMPLOYEE, "Employee"),
        (ROLE_INTERN, "Intern"),
        (ROLE_IT, "IT Support"),
    ]

    role = models.CharField(
        max_length=30, choices=ROLE_CHOICES, default=ROLE_EMPLOYEE)

    def __str__(self):
        return f"{self.username} ({self.role})"


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    otp_hash = models.CharField(max_length=128)  # store hashed OTP only
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    OTP_EXPIRY_MINUTES = 10

    def is_expired(self):
        return timezone.now() > self.created_at + datetime.timedelta(
            minutes=self.OTP_EXPIRY_MINUTES
        )

    def verify_otp(self, raw_otp):
        # Compare hashed OTP securely
        return check_password(raw_otp, self.otp_hash)

    @classmethod
    def create_otp(cls, user, raw_otp):
        # Helper to create hashed OTP
        return cls.objects.create(
            user=user,
            otp_hash=make_password(raw_otp)
        )

    def __str__(self):
        return f"OTP for {self.user.username}"

    class Meta:
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["is_used", "created_at"]),
        ]
