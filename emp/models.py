# emp/models.py
from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.utils import timezone
from .validators import validate_file_size, validate_image_extension
from datetime import timedelta, time
from decimal import Decimal
from .constants import LEAVE_TYPE_CHOICES, EMPLOYEE_DEPARTMENT_CHOICES


User = settings.AUTH_USER_MODEL


class EmployeeProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='employeeprofile')

    emp_id = models.CharField(max_length=20, unique=True)
    work_email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, null=True, blank=True)

    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    middle_name = models.CharField(max_length=80, null=True, blank=True)

    personal_email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    alternate_number = models.CharField(max_length=20, null=True, blank=True)

    dob = models.DateField(null=True, blank=True)
    blood_group = models.CharField(max_length=5, null=True, blank=True)

    gender = models.CharField(max_length=20, null=True, blank=True)
    marital_status = models.CharField(max_length=20, null=True, blank=True)

    profile_photo = models.ImageField(
        upload_to='profile_photos/',
        null=True,
        blank=True,
        validators=[validate_file_size, validate_image_extension]
    )

    aadhaar_number = models.CharField(max_length=12, null=True, blank=True)
    aadhaar_front_image = models.ImageField(
        upload_to='ids/aadhaar/',
        null=True,
        blank=True,
        validators=[validate_file_size, validate_image_extension]
    )
    aadhaar_back_image = models.ImageField(
        upload_to='ids/aadhaar/',
        null=True,
        blank=True,
        validators=[validate_file_size, validate_image_extension]
    )

    pan = models.CharField(max_length=20, null=True, blank=True)
    pan_front_image = models.ImageField(
        upload_to='ids/pan/',
        null=True,
        blank=True,
        validators=[validate_file_size, validate_image_extension]
    )
    pan_back_image = models.ImageField(
        upload_to='ids/pan/',
        null=True,
        blank=True,
        validators=[validate_file_size, validate_image_extension]
    )

    passport_number = models.CharField(max_length=20, null=True, blank=True)
    passport_front_image = models.ImageField(
        upload_to='ids/passport/',
        null=True,
        blank=True,
        validators=[validate_file_size, validate_image_extension]
    )
    passport_back_image = models.ImageField(
        upload_to='ids/passport/',
        null=True,
        blank=True,
        validators=[validate_file_size, validate_image_extension]
    )

    id_card_number = models.CharField(max_length=50, null=True, blank=True)
    id_card_front_image = models.ImageField(
        upload_to='ids/idcard/',
        null=True,
        blank=True,
        validators=[validate_file_size, validate_image_extension]
    )
    id_card_back_image = models.ImageField(
        upload_to='ids/idcard/',
        null=True,
        blank=True,
        validators=[validate_file_size, validate_image_extension]
    )

    job_title = models.CharField(max_length=150, null=True, blank=True)

    department = models.CharField(
        max_length=100, choices=EMPLOYEE_DEPARTMENT_CHOICES, blank=True, null=True)

    designation = models.CharField(max_length=100, null=True, blank=True)
    date_of_joining = models.DateField(null=True, blank=True)

    team_lead = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='assigned_employees'
    )

    def team_lead_display(self):
        if self.team_lead:
            return f"{self.team_lead.first_name} {self.team_lead.last_name}".strip() or self.team_lead.username
        return None

    employment_type = models.CharField(max_length=50, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=150, null=True, blank=True)
    job_description = models.TextField(null=True, blank=True)

    id_image = models.ImageField(
        upload_to='employee/id_cards/',
        null=True,
        blank=True,
        validators=[validate_file_size, validate_image_extension]
    )

    bank_name = models.CharField(max_length=150, null=True, blank=True)
    account_number = models.CharField(max_length=64, null=True, blank=True)
    ifsc_code = models.CharField(max_length=20, null=True, blank=True)
    branch = models.CharField(max_length=150, null=True, blank=True)

    role = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return f"{self.full_name()} ({self.emp_id})"

    def is_on_leave(self, start, end):
        """
        Returns True if this employee has any leave overlapping start..end.
        We exclude rejected leaves.
        """
        from .models import LeaveRequest

        return LeaveRequest.objects.filter(
            profile=self,
        ).exclude(
            status__in=['tl_rejected', 'hr_rejected', 'rejected']
        ).filter(
            start_date__lte=end,
            end_date__gte=start
        ).exists()

    class Meta:
        ordering = ['-created_at']


class Notification(models.Model):
    NOTIF_TYPES = [
        ('announcement', 'Announcement'),
        ('meeting', 'Meeting'),
        ('birthday', 'Birthday'),
        ('anniversary', 'Anniversary'),
        ('leave', 'Leave'),
        ('payroll', 'Payroll'),
        ('policy', 'Policy'),
    ]
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=250)
    body = models.TextField()
    notif_type = models.CharField(
        max_length=50, choices=NOTIF_TYPES, default='announcement')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    extra = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} → {self.to_user}"


class Shift(models.Model):
    name = models.CharField(max_length=120)
    start_time = models.TimeField()
    end_time = models.TimeField()
    total_hours = models.DecimalField(
        max_digits=4, decimal_places=2, default=8.00)
    grace_minutes = models.PositiveIntegerField(default=5)
    late_threshold = models.PositiveIntegerField(default=15)

    def __str__(self):
        return f"{self.name} ({self.start_time}-{self.end_time})"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('working', 'Working'),
        ('present', 'Present'),
        ('halfday', 'Half Day'),
        ('absent', 'Absent'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()

    clock_in = models.DateTimeField()
    clock_out = models.DateTimeField(null=True, blank=True)

    duration_time = models.DurationField(
        max_length=20, null=True, blank=True)
    duration_seconds = models.IntegerField(
        null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='working')
    late_arrivals = models.BooleanField(default=False)
    total_hours = models.DurationField(default=timedelta())
    overtime = models.DurationField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']

    def compute_duration_and_overtime(self, standard_seconds=9*3600):
        if not self.clock_in or not self.clock_out:
            self.duration_time = None
            self.duration_seconds = 0
            self.status = 'working'
            return
        delta = self.clock_out - self.clock_in
        total_seconds = int(delta.total_seconds())
        self.duration_time = delta              # ✅ timedelta
        self.duration_seconds = total_seconds   # ✅ int
        hours = total_seconds / 3600.0
        if hours >= 9:
            self.status = 'present'
        elif 2 <= hours < 9:
            self.status = 'halfday'
        else:
            self.status = 'absent'

    def worked_duration(self):
        if not self.clock_in:
            return timedelta(0)

        end_time = self.clock_out or timezone.now()
        return end_time - self.clock_in


class CalendarEvent(models.Model):
    EVENT_TYPES = [
        ('meeting', 'Meeting'),
        ('announcement', 'Announcement'),
        ('holiday', 'Holiday'),
    ]
    title = models.CharField(max_length=250)
    description = models.TextField(null=True, blank=True)
    event_type = models.CharField(
        max_length=50, choices=EVENT_TYPES, default='announcement')
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    visible_to_tl_hr = models.BooleanField(default=True)
    extra = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-date']


class SalaryStructure(models.Model):
    name = models.CharField(max_length=150)
    monthly_ctc = models.DecimalField(max_digits=12, decimal_places=2)

    basic_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=50.00)
    hra_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=45.00)

    other_allowances = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00
    )

    overtime_multiplier = models.DecimalField(
        max_digits=4, decimal_places=2, default=1.25
    )

    # ✅ COMPANY RULES (DECIMAL SAFE)
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


class EmployeeSalary(models.Model):
    profile = models.OneToOneField(
        EmployeeProfile,
        on_delete=models.CASCADE,
        related_name="salary"
    )
    structure = models.ForeignKey(
        SalaryStructure,
        on_delete=models.PROTECT
    )
    effective_from = models.DateField()
    is_active = models.BooleanField(default=True)

    def hourly_rate(self, working_days_in_month=22, hours_per_day=8):
        basic = self.structure.basic_amount()
        denom = Decimal(working_days_in_month * hours_per_day)
        if denom == 0:
            return Decimal("0.00")
        return basic / denom

    def __str__(self):
        return f"{self.profile.user.username} - {self.structure.name}"


class Payslip(models.Model):
    profile = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.CASCADE,
        related_name="emp_payslips"
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
        related_name="emp_generated_payslips"
    )

    finalized = models.BooleanField(default=False)

    class Meta:
        unique_together = ("profile", "year", "month")
        ordering = ["-year", "-month"]

    def __str__(self):
        return f"Employee Payslip: {self.profile.user.username} - {self.month}/{self.year}"


class LeaveType(models.Model):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class LeaveBalance(models.Model):
    profile = models.ForeignKey(
        EmployeeProfile, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES)
    total_allocated = models.DecimalField(
        max_digits=6, decimal_places=2, default=0.0)
    used = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)

    def available(self):
        return float(self.total_allocated) - float(self.used)

    def __str__(self):
        return f"{self.profile.emp_id} - {self.leave_type.name} : {self.available()}"


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('tl_approved', 'TL Approved'),
        ('tl_rejected', 'TL Rejected'),
        ('hr_approved', 'HR Approved'),
        ('hr_rejected', 'HR Rejected'),
        ('pending_hr', 'Pending HR'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    profile = models.ForeignKey(
        EmployeeProfile, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    days = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField(null=True, blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=30, choices=STATUS_CHOICES, default='applied')
    tl = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                           on_delete=models.SET_NULL, related_name='tl_for_leave')
    hr = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                           on_delete=models.SET_NULL, related_name='hr_for_leave')
    tl_remarks = models.TextField(null=True, blank=True)
    hr_remarks = models.TextField(null=True, blank=True)
    last_action_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                       blank=True, on_delete=models.SET_NULL, related_name='leave_actions')
    last_action_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-applied_at']

    def apply_tl_approval(self, approver_user, approve: bool, remarks: str = None):
        """
        Team Lead approval logic.
        Action must be explicit: approve=True or approve=False.
        No implicit rejection is allowed.
        """

        if self.status != "applied":
            raise ValidationError(
                "TL action is allowed only when leave status is 'applied'."
            )

        if self.last_action_by == approver_user:
            raise ValidationError(
                "This leave has already been acted upon by you."
            )

        if approve is not True and approve is not False:
            raise ValidationError(
                "TL action must be explicitly approve or reject.")

        self.tl = approver_user
        self.tl_remarks = remarks or ""
        self.last_action_by = approver_user
        self.last_action_at = timezone.now()

        if approve is True:
            self.status = "tl_approved"
        else:
            self.status = "tl_rejected"

        self.save(
            update_fields=[
                "status",
                "tl",
                "tl_remarks",
                "last_action_by",
                "last_action_at",
            ]
        )

    def apply_hr_approval(self, approver_user, approve: bool, remarks: str = None):
        """
        HR approval logic.
        HR can act ONLY after TL approval.
        Action must be explicit.
        """

        if self.status in ("hr_approved", "hr_rejected"):
            raise ValidationError(
                "Leave process already completed. No further action allowed."
            )

        if self.status != "tl_approved":
            raise ValidationError(
                "HR action is allowed only after TL approval."
            )

        if approve is not True and approve is not False:
            raise ValidationError(
                "HR action must be explicitly approve or reject.")

        self.hr = approver_user
        self.hr_remarks = remarks or ""
        self.last_action_by = approver_user
        self.last_action_at = timezone.now()

        if approve is True:
            self.status = "hr_approved"
        else:
            self.status = "hr_rejected"

        self.save(
            update_fields=[
                "status",
                "hr",
                "hr_remarks",
                "last_action_by",
                "last_action_at",
            ]
        )


class Policy(models.Model):
    POLICY_TYPES = [
        ('policy', 'Company Policy'),
        ('terms', 'Terms & Conditions'),
        ('resignation', 'Resignation Rules'),
        ('separation', 'Separation Rules'),
    ]
    title = models.CharField(max_length=250)
    policy_type = models.CharField(
        max_length=50, choices=POLICY_TYPES, default='policy')
    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class TimesheetDay(models.Model):
    profile = models.ForeignKey(
        'EmployeeProfile', on_delete=models.CASCADE, related_name='timesheet_days'
    )
    date = models.DateField()

    attendance = models.OneToOneField(
        'Attendance',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='timesheet_day'
    )

    clock_in = models.DateTimeField(null=True, blank=True)
    clock_out = models.DateTimeField(null=True, blank=True)

    is_submitted = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)

    last_modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='modified_timesheets'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('profile', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.profile.emp_id} - {self.date}"


class TimesheetEntry(models.Model):
    """
    Task-level timesheet entry for a specific employee and date.
    This implementation is self-contained and uses TimesheetDay for clock-in/out metadata.
    """
    profile = models.ForeignKey(
        'EmployeeProfile', on_delete=models.CASCADE, related_name='timesheet_entries')
    date = models.DateField()
    day = models.CharField(max_length=20, blank=True)
    task = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_seconds = models.IntegerField(null=True, blank=True)
    manual = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    project_task = models.ForeignKey(
        'projects.Task',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='timesheet_entries'
    )

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ('profile', 'date', 'start_time', 'end_time')

    def clean(self):

        if self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time.")
        if self.start_time.date() != self.date or self.end_time.date() != self.date:
            raise ValidationError(
                "Start and end must be on the same date as the 'date' field.")

        if (self.end_time - self.start_time).total_seconds() > 6 * 3600:
            raise ValidationError(
                "Single task duration should not exceed 6 hours. Split into smaller tasks.")

        qs = TimesheetEntry.objects.filter(profile=self.profile, date=self.date).exclude(
            pk=self.pk).order_by('start_time')
        for e in qs:

            if not (self.end_time <= e.start_time or self.start_time >= e.end_time):
                raise ValidationError(
                    "Time entry overlaps another entry for the same day. Please fix the times.")

    def save(self, *args, **kwargs):

        if not self.day:
            self.day = self.date.strftime("%A")

        if self.start_time and self.end_time:
            self.duration_seconds = int(
                (self.end_time - self.start_time).total_seconds())

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{getattr(self.profile, 'emp_id', self.profile.id)} {self.date} {self.task}"
