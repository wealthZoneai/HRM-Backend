from django.db import models
from django.conf import settings   # ✅ Use this instead of User


class LongLeave(models.Model):

    LEAVE_TYPE_CHOICES = [
        ('Medical', 'Medical Leave'),
        ('Suspended', 'Suspended'),
        ('Maternity', 'Maternity/Paternity'),
        ('Personal', 'Personal Leave'),
    ]

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,   # ✅ Correct way
        on_delete=models.CASCADE,
        related_name='long_leaves'
    )

    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee} - {self.leave_type}"

#Reports
from django.db import models
class Client(models.Model):
    name = models.CharField(max_length = 100)

    def __str__(self):
        return self.name

class DeliveryManager(models.Model):
    name = models.CharField(max_length = 100)

    def __str__(self):
        return self.name

class Project(models.Model):
    client = models.ForeignKey(Client, on_delete = models.CASCADE)
    project = models.CharField(max_length = 100)
    delivery = models.ForeignKey(DeliveryManager, on_delete = models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    completion = models.IntegerField()
    status = models.CharField(max_length=50)

    def __str__(self):
        return self.project


class ModuleProgress(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    module_name = models.CharField(max_length=100)
    progress = models.IntegerField()

    def __str__(self):
        return self.module_name
    

class RiskAlert(models.Model):

    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    message = models.CharField(max_length=200)

    level = models.CharField(
        max_length=20,
        choices=[
            ("warning", "Warning"),
            ("critical", "Critical")
        ]
    )

    def __str__(self):
        return self.message