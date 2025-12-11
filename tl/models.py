# tl/models.py
# TL app depends on emp.models, no models required.
# tl/models.py
from django.db import models
from django.conf import settings

class TLAnnouncement(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    priority = models.CharField(max_length=10)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tl_created_announcements"
    )

    def __str__(self):
        return self.title
