# hr/models.py
from django.db import models
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from .constants import ANNOUNCEMENT_AUDIENCE_CHOICES


class Announcement(models.Model):

    PRIORITY_CHOICES = [
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    audience = models.CharField(max_length=50, choices=ANNOUNCEMENT_AUDIENCE_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    show_in_calendar = models.BooleanField(default=True)

    class Meta:
        models.UniqueConstraint(
            fields=['date', 'time'],
            name='unique_announcement_datetime'
        )

    def __str__(self):
        return self.title


class TLAnnouncement(models.Model):
    PRIORITY_CHOICES = [
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tl_announcements'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    show_in_calendar = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class SalaryStructure(models.Model):
    name = models.CharField(max_length=150)
    monthly_ctc = models.DecimalField(max_digits=12, decimal_places=2)

    basic_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=50.00
    )
    hra_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=22.50
    )

    other_allowances = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00
    )

    overtime_multiplier = models.DecimalField(
        max_digits=4, decimal_places=2, default=1.25
    )

    # 🔹 CALCULATIONS (ALL DECIMAL SAFE)
    def basic_amount(self):
        return self.monthly_ctc * (self.basic_percent / Decimal("100"))

    def hra_amount(self):
        return self.monthly_ctc * (self.hra_percent / Decimal("100"))

    def pf_amount(self):
        # PF = 50% of BASIC
        return self.basic_amount() * Decimal("0.50")

    def gross_amount(self):
        return self.monthly_ctc

    def __str__(self):
        return f"{self.name} ({self.monthly_ctc})"


class Payslip(models.Model):
    profile = models.ForeignKey(
        "emp.EmployeeProfile",
        on_delete=models.CASCADE,
        related_name="hr_payslips"
    )

    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()

    working_days = models.PositiveIntegerField(default=0)
    days_present = models.PositiveIntegerField(default=0)

    gross_amount = models.DecimalField(max_digits=12, decimal_places=2)
    overtime_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00
    )
    deductions = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00
    )
    net_amount = models.DecimalField(max_digits=12, decimal_places=2)

    details = models.JSONField(null=True, blank=True)

    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="hr_generated_payslips"
    )

    finalized = models.BooleanField(default=False)

    class Meta:
        unique_together = ("profile", "year", "month")
        ordering = ["-year", "-month"]

    def __str__(self):
        return f"HR Payslip: {self.profile.user.username} - {self.month}/{self.year}"
