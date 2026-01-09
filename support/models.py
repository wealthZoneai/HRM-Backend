from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class SupportTicket(models.Model):
    CATEGORY_CHOICES = [
        ('HR', 'HR'),
        ('IT', 'IT'),
        ('PAYROLL', 'Payroll'),
        ('PROJECT', 'Project'),
        ('OTHER', 'Other'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]

    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('WAITING', 'Waiting for User'),
        ('CLOSED', 'Closed'),
    ]

    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='support_tickets'
    )

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM'
    )

    subject = models.CharField(max_length=200)

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='OPEN'
    )

    assigned_to = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_tickets'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"#{self.id} {self.subject}"

class SupportMessage(models.Model):
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name='messages'
    )

    sender = models.ForeignKey(
        User, on_delete=models.CASCADE
    )

    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

class LoginSupportTicket(models.Model):
    email_or_empid = models.CharField(max_length=150)
    issue_type = models.CharField(max_length=100)
    message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

class LoginSupportTicket(models.Model):
    ISSUE_CHOICES = [
        ('OTP', 'OTP not received'),
        ('PASSWORD', 'Forgot password'),
        ('LOCKED', 'Account locked'),
        ('LOGIN', 'Unable to login'),
        ('OTHER', 'Other'),
    ]

    email_or_empid = models.CharField(max_length=150)
    issue_type = models.CharField(max_length=20, choices=ISSUE_CHOICES)
    message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.email_or_empid} - {self.issue_type}"
