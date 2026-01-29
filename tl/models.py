# tl/models.py
from django.db import models
from django.conf import settings


class TLAnnouncement(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    priority = models.CharField(max_length=10)
    created_role = models.CharField(max_length=20, default="TL")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tl_created_announcements"
    )

    show_in_calendar = models.BooleanField(default=True)

    class Meta:
        models.UniqueConstraint(
            fields=['date', 'time'],
            name='unique_announcement_datetime'
        )

    def __str__(self):
        return self.title

class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=['date', 'time'],
            name='unique_announcement_datetime'
        )
    ]