# hr/models.py
from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.conf import settings
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
    department = models.CharField(max_length=50)
    location = models.CharField(max_length=255, blank=True, null=True)
    # audience = models.CharField(max_length=50, choices=ANNOUNCEMENT_AUDIENCE_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    show_in_calendar = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["date", "time"],
                name="unique_hr_announcement_datetime"
            )
        ]

    def __str__(self):
        return self.title
