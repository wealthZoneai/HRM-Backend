from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class EmployeeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Contact
    work_email = models.EmailField(unique=True, null=True, blank=True)
    personal_email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    emp_id = models.CharField(max_length=20, unique=True)

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)

    # Job Info
    job_title = models.CharField(max_length=100, null=True, blank=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='manages',
                                null=True, blank=True, on_delete=models.SET_NULL)
    employment_type = models.CharField(max_length=50, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    job_description = models.TextField(null=True, blank=True)

    # Bank
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    account_number = models.CharField(max_length=50, null=True, blank=True)
    ifsc_code = models.CharField(max_length=20, null=True, blank=True)
    branch = models.CharField(max_length=100, null=True, blank=True)

    # IDs
    aadhaar = models.CharField(max_length=20, null=True, blank=True)
    pan = models.CharField(max_length=20, null=True, blank=True)
    id_card = models.CharField(max_length=100, null=True, blank=True)

    passport_image = models.ImageField(
        upload_to='passport/', null=True, blank=True)
    id_card_image = models.ImageField(
        upload_to='id_cards/', null=True, blank=True)
    aadhaar_image = models.ImageField(
        upload_to='aadhaar/', null=True, blank=True)
    pan_image = models.ImageField(upload_to='pan/', null=True, blank=True)

    profile_photo = models.ImageField(
        upload_to='profile_photos/', null=True, blank=True)

    role = models.CharField(max_length=20, default="employee")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.emp_id})"


class Attendance(models.Model):
    STATUS_CHOICES = (
        ('in_progress', 'In Progress'),  # clocked in, not yet clocked out
        ('completed', 'Completed'),      # clocked out
    )

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()  # local date of the attendance (derived from clock_in)
    clock_in = models.DateTimeField()
    clock_out = models.DateTimeField(blank=True, null=True)
    duration_seconds = models.PositiveIntegerField(
        blank=True, null=True)  # seconds between in/out
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='in_progress')
    # optional note on clock-out/clock-in
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # one attendance row per user per date
        unique_together = ('user', 'date')
        ordering = ['-date', '-clock_in']

    def __str__(self):
        return f"{self.user} — {self.date} — {self.status}"
