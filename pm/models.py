from django.db import models
from django.conf import settings


# -------------------------
# TEAM LEAD
# -------------------------
class TeamLead(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    active_projects = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username


# -------------------------
# PROJECT
# -------------------------
class Project(models.Model):

    STATUS_CHOICES = [
        ('new', 'New'),
        ('inprogress', 'In Progress'),
        ('completed', 'Completed')
    ]

    name = models.CharField(max_length=200)

    client = models.CharField(max_length=200)

    deadline = models.DateField()

    delivery_manager = models.CharField(max_length=200)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )

    team_lead = models.ForeignKey(
        TeamLead,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# -------------------------
# TASK (For Tasks Page + Workboard)
# -------------------------
class Task(models.Model):

    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('inprogress', 'In Progress'),
        ('done', 'Done'),
        ('blocked', 'Blocked')
    ]

    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('critical', 'Critical')
    ]

    title = models.CharField(max_length=255)

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='todo'
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )

    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    due_date = models.DateField()

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# -------------------------
# RISK MODULE
# -------------------------
class Risk(models.Model):

    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('critical', 'Critical')
    ]

    title = models.CharField(max_length=200)

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="risks"
    )

    description = models.TextField()

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# -------------------------
# TIMELINE TASK
# -------------------------
class TimelineTask(models.Model):

    STATUS_CHOICES = [
        ("completed", "Completed"),
        ("upcoming", "Upcoming"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="timeline_tasks"
    )

    title = models.CharField(max_length=200)

    due_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="upcoming"
    )

    dependency = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.title


# -------------------------
# TEAM MEMBER (Workload Board)
# -------------------------
class TeamMember(models.Model):

    STATUS_CHOICES = [
        ("available", "Available"),
        ("busy", "Busy"),
        ("away", "Away"),
        ("break", "Be Right Back")
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    role = models.CharField(max_length=100)

    workload = models.IntegerField(
        help_text="Workload percentage"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="available"
    )

    profile_image = models.ImageField(
        upload_to="team_profiles/",
        blank=True,
        null=True
    )

    def __str__(self):
        return self.user.username