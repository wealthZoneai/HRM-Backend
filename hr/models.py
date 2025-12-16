# hr/models.py
from django.db import models
from django.utils import timezone
from django.conf import settings


class Announcement(models.Model):
    DEPARTMENT_CHOICES = [
        ("HR", "Human Resources"),
        ("EMP", "Employee"),
        ("TL", "Team Lead"),
        ("FIN", "Finance"),
        ("MKT", "Marketing"),
        ("IT", "IT Department"),
    ]

    PRIORITY_CHOICES = [
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    show_in_calendar = models.BooleanField(default=True)

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
