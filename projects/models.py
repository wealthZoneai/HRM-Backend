from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from login.models import User as LoginUser

User = settings.AUTH_USER_MODEL


class Project(models.Model):
    STATUS = [
        ('draft', 'Draft'),
        ('assigned_pm', 'Assigned to PM'),
        ('in_progress', 'In Progress'),
        ('at_risk', 'At Risk'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('closed', 'Closed'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    delivery_manager = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='dm_projects'
    )
    project_manager = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.PROTECT, related_name='pm_projects'
    )

    status = models.CharField(
        max_length=30, choices=STATUS, default='draft'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def assign_pm(self, user):
        if self.status != 'draft':
            raise ValidationError("PM can only be assigned in Draft state.")
        self.project_manager = user
        self.status = 'assigned_pm'
        self.save(update_fields=['project_manager', 'status'])


class ProjectModule(models.Model):
    STATUS = [
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('blocked', 'Blocked'),
        ('completed', 'Completed'),
        ('returned', 'Returned'),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='modules'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    team_lead = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='project_modules'
    )

    status = models.CharField(
        max_length=30, choices=STATUS, default='assigned'
    )


class Task(models.Model):
    STATUS = [
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('review', 'Review'),
        ('rework', 'Rework'),
        ('completed', 'Completed'),
    ]

    module = models.ForeignKey(
        ProjectModule, on_delete=models.CASCADE, related_name='tasks'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    assigned_to = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='tasks'
    )
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='created_tasks'
    )

    status = models.CharField(
        max_length=30, choices=STATUS, default='assigned'
    )

    assigned_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)

    def mark_completed(self, user):
        if user.role != LoginUser.ROLE_TL:
            raise ValidationError("Only TL can complete a task.")
        if self.subtasks.exclude(status='completed').exists():
            raise ValidationError("All subtasks must be completed.")
        self.status = 'completed'
        self.save(update_fields=['status'])


class SubTask(models.Model):
    STATUS = [
        ('created', 'Created'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]

    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name='subtasks'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='subtasks'
    )
    status = models.CharField(
        max_length=30, choices=STATUS, default='created'
    )

    approved_by_tl = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='approved_subtasks'
    )


class ProjectAudit(models.Model):
    ACTION_CHOICES = [
        ('project_status', 'Project Status Change'),
        ('module_status', 'Module Status Change'),
        ('task_status', 'Task Status Change'),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES
    )

    old_value = models.CharField(max_length=50)
    new_value = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.name} | {self.action} | {self.old_value} → {self.new_value}"
