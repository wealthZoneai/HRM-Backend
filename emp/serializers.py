# emp/serializers.py
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from login import models
from .models import (
    EmployeeProfile, Notification, Shift, Attendance, CalendarEvent,
    SalaryStructure, EmployeeSalary, Payslip,
    LeaveType, LeaveBalance, LeaveRequest, Policy
)
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.urls import reverse
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

User = get_user_model()


class ContactSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True, max_length=80)
    middle_name = serializers.CharField(
        required=False, allow_blank=True, max_length=80)
    last_name = serializers.CharField(required=True, max_length=80)
    personal_email = serializers.EmailField(required=True)
    phone_number = serializers.CharField(required=True, max_length=20)
    alternate_number = serializers.CharField(
        required=False, allow_blank=True, max_length=20)
    dob = serializers.DateField(required=True)
    blood_group = serializers.CharField(
        required=False, allow_blank=True, max_length=5)
    gender = serializers.ChoiceField(
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], required=True)
    marital_status = serializers.ChoiceField(choices=[(
        'single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced')], required=False)
    profile_photo = serializers.ImageField(required=False, allow_null=True)


class JobSerializer(serializers.Serializer):
    job_title = serializers.CharField(required=True, max_length=150)
    department = serializers.CharField(required=True)
    team_lead = serializers.CharField(
        required=False, allow_blank=True, allow_null=True)
    employment_type = serializers.ChoiceField(choices=[(
        'full_time', 'Full Time'), ('contract', 'Contract')], required=True)
    start_date = serializers.DateField(required=True)
    location = serializers.CharField(
        required=False, allow_blank=True, max_length=200)
    job_description = serializers.CharField(required=False, allow_blank=True)
    id_image = serializers.ImageField(required=False, allow_null=True)


class BankSerializer(serializers.Serializer):
    bank_name = serializers.CharField(required=True, max_length=150)
    ifsc_code = serializers.CharField(required=True, max_length=20)
    account_number = serializers.CharField(required=True, max_length=50)
    confirm_account_number = serializers.CharField(
        required=True, max_length=50)
    branch = serializers.CharField(required=True, max_length=150)

    def validate(self, data):
        if data.get('account_number') != data.get('confirm_account_number'):
            raise serializers.ValidationError(
                {"confirm_account_number": "Account numbers do not match."})
        return data


class IdentificationSerializer(serializers.Serializer):
    aadhaar_number = serializers.CharField(
        required=False, allow_blank=True, max_length=32)
    aadhaar_image = serializers.ImageField(required=False, allow_null=True)
    pan_number = serializers.CharField(
        required=False, allow_blank=True, max_length=20)
    pan_image = serializers.ImageField(required=False, allow_null=True)
    passport_number = serializers.CharField(
        required=False, allow_blank=True, max_length=20)
    passport_image = serializers.ImageField(required=False, allow_null=True)


class EmployeeCreateSerializer(serializers.Serializer):
    # minimal user info (keeps backward compatibility)
    role = serializers.ChoiceField(
        choices=[
            ('employee', 'Employee'),
            ('intern', 'Intern'),
            ('tl', 'Team Leader'),
            ('hr', 'HR'),
            ('management', 'Management')
        ],
        default='employee'
    )
    emp_id = serializers.CharField(
        required=False, allow_blank=True, max_length=50)
    work_email = serializers.EmailField(required=False, allow_blank=True)

    # nested sections
    contact = ContactSerializer(required=True)
    job = JobSerializer(required=True)
    bank = BankSerializer(required=True)
    identification = IdentificationSerializer(required=False)

    # ----------------------------------------------------------------------
    # FIELD-LEVEL VALIDATION
    # ----------------------------------------------------------------------
    def validate_work_email(self, value):
        if value and User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "User with this email already exists.")
        return value

    # ----------------------------------------------------------------------
    # OBJECT-LEVEL VALIDATION (TEAM LEAD OPTIONAL BUT MUST BE VALID IF PROVIDED)
    # ----------------------------------------------------------------------
    def validate(self, data):
        """
        Validate job.team_lead only if provided.
        TL is optional in employee creation. If provided, it must resolve to a valid User.
        """
        job = data.get('job', {}) or {}
        tl_val = job.get('team_lead')

        # TL is optional → allow employee creation without assigning TL
        if not tl_val:
            return data

        # Try resolving TL to a user
        try:
            if str(tl_val).isdigit():
                user = User.objects.filter(id=int(tl_val)).first()
            else:
                user = (
                    User.objects.filter(username__iexact=tl_val).first()
                    or User.objects.filter(email__iexact=tl_val).first()
                )
        except Exception:
            user = None

        # If TL value exists but cannot be resolved → throw error
        if not user:
            raise ValidationError({
                "job": {
                    "team_lead": "Invalid team_lead: user not found (provide user id, username or email)."
                }
            })

        if user.role != 'tl':
            raise ValidationError({
                "job": {
                    "team_lead": f"Invalid selection: '{user.username}' is not a Team Lead."
                }
            })

        # Normalize TL value → replace provided value with the resolved user.id
        data.setdefault('job', {})['team_lead'] = user.id
        return data

    # ----------------------------------------------------------------------
    # CREATE LOGIC
    # ----------------------------------------------------------------------
    def create(self, validated_data):
        contact = validated_data.get('contact', {})
        job = validated_data.get('job', {})
        bank = validated_data.get('bank', {})
        identification = validated_data.get('identification', {})

        # basic info
        first_name = (contact.get('first_name') or '').strip()
        last_name = (contact.get('last_name') or '').strip()
        role = validated_data.get('role', 'employee')
        email = (validated_data.get('work_email') or '').strip() or None

        # username generation
        base_username = f"{first_name.lower()}.{last_name.lower()}" if first_name or last_name else "user"
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # create User
        user = User.objects.create_user(
            username=username,
            password=None,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=role
        )
        user.set_unusable_password()
        user.save()

        # create/get EmployeeProfile
        prof, created = EmployeeProfile.objects.get_or_create(
            user=user,
            defaults={
                'emp_id': validated_data.get('emp_id') or '',
                'work_email': email or '',
                'first_name': first_name or '',
                'last_name': last_name or '',
                'role': role
            }
        )

        # update fields
        if validated_data.get('emp_id'):
            prof.emp_id = validated_data.get('emp_id')

        # CONTACT
        prof.first_name = first_name or prof.first_name
        prof.middle_name = contact.get('middle_name') or prof.middle_name
        prof.last_name = last_name or prof.last_name
        prof.personal_email = contact.get(
            'personal_email') or prof.personal_email
        prof.phone_number = contact.get('phone_number') or prof.phone_number
        prof.alternate_number = contact.get(
            'alternate_number') or prof.alternate_number
        prof.dob = contact.get('dob') or prof.dob
        prof.blood_group = contact.get('blood_group') or prof.blood_group
        prof.gender = contact.get('gender') or prof.gender
        prof.marital_status = contact.get(
            'marital_status') or prof.marital_status
        if contact.get('profile_photo') is not None:
            prof.profile_photo = contact.get('profile_photo')

        # JOB
        prof.job_title = job.get('job_title') or prof.job_title
        prof.department = job.get('department')

        # team_lead already normalized in validate() → always integer id if provided
        tl_val = job.get('team_lead')
        if tl_val:
            prof.team_lead_id = int(tl_val)

        prof.employment_type = job.get(
            'employment_type') or prof.employment_type
        prof.start_date = job.get('start_date') or prof.start_date
        prof.location = job.get('location') or prof.location
        prof.job_description = job.get(
            'job_description') or prof.job_description
        if job.get('id_image') is not None:
            prof.id_image = job.get('id_image')

        # BANK
        prof.bank_name = bank.get('bank_name') or prof.bank_name
        prof.ifsc_code = bank.get('ifsc_code') or prof.ifsc_code
        prof.account_number = bank.get('account_number') or prof.account_number
        prof.branch = bank.get('branch') or prof.branch

        # IDENTIFICATION
        prof.aadhaar_number = identification.get(
            'aadhaar_number') or prof.aadhaar_number
        if identification.get('aadhaar_image') is not None:
            prof.aadhaar_image = identification.get('aadhaar_image')
        prof.pan = identification.get('pan_number') or prof.pan
        if identification.get('pan_image') is not None:
            prof.pan_image = identification.get('pan_image')
        prof.passport_number = identification.get(
            'passport_number') or prof.passport_number
        if identification.get('passport_image') is not None:
            prof.passport_image = identification.get('passport_image')

        # work_email
        if email:
            prof.work_email = email

        # save minimal fields
        update_fields = [
            'emp_id', 'work_email', 'first_name', 'middle_name', 'last_name',
            'personal_email', 'phone_number', 'alternate_number', 'dob',
            'blood_group', 'gender', 'marital_status',
            'job_title', 'department', 'team_lead', 'employment_type',
            'start_date', 'location', 'job_description', 'id_image',
            'bank_name', 'ifsc_code', 'account_number', 'branch',
            'aadhaar_number', 'aadhaar_image', 'pan', 'pan_image',
            'passport_number', 'passport_image', 'profile_photo'
        ]
        valid_update_fields = [f for f in update_fields if hasattr(prof, f)]
        prof.save(update_fields=valid_update_fields)

        return user, prof

    def save(self, **kwargs):
        return self.create(self.validated_data)


class EmployeeProfileReadSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    masked_aadhaar = serializers.SerializerMethodField()
    masked_pan = serializers.SerializerMethodField()
    masked_passport = serializers.SerializerMethodField()
    masked_account_number = serializers.SerializerMethodField()

    protected_profile_photo_url = serializers.SerializerMethodField()
    protected_aadhaar_image_url = serializers.SerializerMethodField()
    protected_pan_image_url = serializers.SerializerMethodField()
    protected_passport_image_url = serializers.SerializerMethodField()
    protected_id_image_url = serializers.SerializerMethodField()

    team_lead = serializers.SerializerMethodField()
    team_lead_id = serializers.SerializerMethodField()

    def mask_number(self, value):
        if not value:
            return value
        return "*" * (len(value) - 4) + value[-4:]

    def get_masked_aadhaar(self, obj):
        return self.mask_number(obj.aadhaar_number)

    def get_masked_pan(self, obj):
        return self.mask_number(obj.pan)

    def get_masked_passport(self, obj):
        return self.mask_number(obj.passport_number)

    def get_masked_account_number(self, obj):
        return self.mask_number(obj.account_number)

    def get_protected_profile_photo_url(self, obj):
        request = self.context.get("request", None)
        try:
            url = reverse("protected_employee_media",
                          args=[obj.pk, "profile_photo"])
        except Exception:
            return None
        if request:
            return request.build_absolute_uri(url)
        # fallback: build a relative url
        return url

    def get_protected_aadhaar_image_url(self, obj):
        request = self.context.get("request", None)
        try:
            url = reverse("protected_employee_media",
                          args=[obj.pk, "aadhaar_image"])
        except Exception:
            return None
        if request:
            return request.build_absolute_uri(url)
        return url

    def get_protected_pan_image_url(self, obj):
        request = self.context.get("request", None)
        try:
            url = reverse("protected_employee_media",
                          args=[obj.pk, "pan_image"])
        except Exception:
            return None
        if request:
            return request.build_absolute_uri(url)
        return url

    def get_protected_passport_image_url(self, obj):
        request = self.context.get("request", None)
        try:
            url = reverse("protected_employee_media",
                          args=[obj.pk, "passport_image"])
        except Exception:
            return None
        if request:
            return request.build_absolute_uri(url)
        return url

    def get_protected_id_image_url(self, obj):
        request = self.context.get("request", None)
        try:
            url = reverse("protected_employee_media",
                          args=[obj.pk, "id_image"])
        except Exception:
            return None
        if request:
            return request.build_absolute_uri(url)
        return url

    def get_team_lead(self, obj):
        if obj.team_lead:
            return {
                "id": obj.team_lead.id,
                "username": obj.team_lead.username,
                "first_name": obj.team_lead.first_name,
                "last_name": obj.team_lead.last_name,
                "email": obj.team_lead.email,
                "display": obj.team_lead.first_name + ' ' + obj.team_lead.last_name if (obj.team_lead.first_name or obj.team_lead.last_name) else obj.team_lead.username
            }
        return None

    def get_team_lead_id(self, obj):
        return obj.team_lead.id if obj.team_lead else None

    def get_user(self, obj):
        return {
            "id": obj.user.id,
            "username": obj.user.username,
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name,
            "email": obj.user.email,
            "role": obj.user.role,
        }

    class Meta:
        model = EmployeeProfile
        fields = (
            'user', 'emp_id', 'work_email', 'first_name', 'middle_name', 'last_name',
            'personal_email', 'phone_number', 'alternate_number', 'dob', 'blood_group',
            'gender', 'marital_status',
            'job_title', 'department', 'team_lead', 'team_lead_id', 'employment_type', 'start_date',
            'location', 'job_description', 'protected_id_image_url', 'protected_profile_photo_url',
            'bank_name', 'ifsc_code', 'masked_account_number', 'branch',
            'masked_aadhaar', 'protected_aadhaar_image_url', 'masked_pan', 'protected_pan_image_url', 'masked_passport', 'protected_passport_image_url',
            'role', 'created_at', 'updated_at'
        )
        read_only_fields = ('emp_id', 'work_email', 'user', 'team_lead', 'team_lead_id',
                            'created_at', 'updated_at')


class EmployeeContactUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeProfile
        fields = ('personal_email', 'phone_number', 'alternate_number',
                  'dob', 'blood_group', 'gender', 'marital_status', 'profile_photo')


class EmployeeIdentificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeProfile
        fields = ('aadhaar_number', 'pan', 'passport_number',
                  'aadhaar_image', 'pan_image', 'passport_image')


# Notifications


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'title', 'body', 'notif_type',
                  'is_read', 'created_at', 'extra')


# Attendance / Shift


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = '__all__'


class AttendanceReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'


# Calendar


class CalendarEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = '__all__'

# Payroll


class SalaryStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryStructure
        fields = '__all__'


class EmployeeSalarySerializer(serializers.ModelSerializer):
    structure = SalaryStructureSerializer(read_only=True)

    class Meta:
        model = EmployeeSalary
        fields = '__all__'


class PayslipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payslip
        fields = '__all__'

# Leave


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'


class LeaveBalanceSerializer(serializers.ModelSerializer):
    available = serializers.SerializerMethodField()

    class Meta:
        model = LeaveBalance
        fields = ('id', 'leave_type', 'total_allocated', 'used', 'available')

    def get_available(self, obj):
        return float(obj.total_allocated) - float(obj.used)


class LeaveRequestSerializer(serializers.ModelSerializer):
    profile = EmployeeProfileReadSerializer(read_only=True)

    class Meta:
        model = LeaveRequest
        fields = ('id', 'profile', 'leave_type', 'start_date', 'end_date', 'days',
                  'reason', 'applied_at', 'status', 'tl', 'hr', 'tl_remarks', 'hr_remarks')


class LeaveApplySerializer(serializers.Serializer):
    leave_type = serializers.CharField(
        max_length=120)   # label from frontend dropdown
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    reason = serializers.CharField(allow_blank=True, required=False)

    def validate(self, data):
        """
        - Ensure start/end date sanity
        - Check for overlapping leave requests for the same profile
        - Verify leave_type exists
        - Verify the profile has sufficient available balance for the requested days
        NOTE: serializer expects the request in self.context['request'] so the profile can be accessed.
        """
        from django.db.models import Q
        from decimal import Decimal
        today = timezone.localdate()
        start = data.get('start_date')
        end = data.get('end_date')

        if start < today:
            raise serializers.ValidationError(
                {"start_date": "Start date cannot be in the past."})
        if end < start:
            raise serializers.ValidationError(
                {"end_date": "End date cannot be before start date."})

        # compute inclusive days (integer)
        requested_days = (end - start).days + 1

        # Require request in context so we can access the user/profile
        req = self.context.get('request')
        if not req or not getattr(req, 'user', None):
            # If no request present, fail-safe: allow (but log). Prefer having request in context.
            return data

        profile = getattr(req.user, 'employeeprofile', None)
        if not profile:
            raise serializers.ValidationError(
                "Employee profile not found for current user.")

        # 1) Overlap check: any non-rejected leaves that overlap with start..end
        overlapping = models.LeaveRequest.objects.filter(
            profile=profile
        ).exclude(status__in=['tl_rejected', 'hr_rejected', 'rejected']).filter(
            start_date__lte=end,
            end_date__gte=start
        ).exists()

        if overlapping:
            raise serializers.ValidationError(
                {"non_field_errors": "You already have a leave request that overlaps these dates."}
            )

        # 2) Validate leave_type exists (case-insensitive)
        leave_type_name = data.get('leave_type', '').strip()
        lt = models.LeaveType.objects.filter(
            name__iexact=leave_type_name).first()
        if not lt:
            raise serializers.ValidationError(
                {"leave_type": f"Leave type '{leave_type_name}' not found."}
            )

        # 3) Check leave balance if available
        lb = models.LeaveBalance.objects.filter(
            profile=profile, leave_type=lt).first()
        if lb:
            # compute available as Decimal
            try:
                available = Decimal(lb.total_allocated) - Decimal(lb.used)
            except Exception:
                # defensive fallback
                available = None
            if available is not None:
                if Decimal(requested_days) > available:
                    raise serializers.ValidationError(
                        {"non_field_errors": f"Insufficient leave balance for '{lt.name}'. Requested: {requested_days}, Available: {available}."}
                    )
        # if no LeaveBalance found we allow apply (allocations may be done later by HR)
        # but you may choose to block instead by uncommenting the lines below:
        # else:
        #     raise serializers.ValidationError({"leave_type": "No leave balance configured for this leave type. Contact HR."})

        # attach computed days for the view to reuse (optional)
        data['calculated_days'] = requested_days
        # also attach normalized leave_type object name (frontend may send different casing)
        data['normalized_leave_type'] = lt.name

        return data


# Policies


class PolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = Policy
        fields = '__all__'






# emp/serializers.py
from rest_framework import serializers
from django.utils import timezone
from rest_framework.exceptions import ValidationError

# IMPORTANT:
# If Attendance model lives in a different app, change the import below:
# from attendance.models import Attendance
from .models import TimesheetEntry, TimesheetDay, Attendance  # adjust if Attendance is elsewhere


# -------------------------
# Per-entry serializer
# -------------------------
class TimesheetEntrySerializer(serializers.ModelSerializer):
    duration_hours = serializers.SerializerMethodField()
    # duration_seconds will be returned as HH:MM:SS string
    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = TimesheetEntry
        fields = [
            "id", "date", "day",
            "task", "description",
            "start_time", "end_time",
            "duration_seconds",
            "duration_hours",
            "created_at", "updated_at",
        ]
        read_only_fields = ["duration_seconds", "duration_hours", "created_at", "updated_at"]

    def _get_total_seconds_safe(self, obj):
        """Return int seconds even if DB contains string or None."""
        try:
            return int(obj.duration_seconds) if obj.duration_seconds is not None else 0
        except (TypeError, ValueError):
            return 0

    def get_duration_hours(self, obj):
        total = self._get_total_seconds_safe(obj)
        return round(total / 3600.0, 2)

    def get_duration_seconds(self, obj):
        total = self._get_total_seconds_safe(obj)
        hours = total // 3600
        minutes = (total % 3600) // 60
        seconds = total % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


# -------------------------
# TimesheetDay serializer
# -------------------------
class TimesheetDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = TimesheetDay
        fields = ("date", "clock_in", "clock_out", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")


# -------------------------
# Input item for batch update
# -------------------------
class TimesheetEntryItemSerializer(serializers.Serializer):
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    task = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)


# -------------------------
# Daily update serializer
# -------------------------
class DailyTimesheetUpdateSerializer(serializers.Serializer):
    """
    Payload:
      {
        "entries": [
          {"start_time": "...", "end_time": "...", "task": "...", "description": "..."},
          ...
        ]
      }

    Business rules enforced:
      - entries list required and not empty
      - entries must be for today's date
      - each entry end_time > start_time
      - max 6 hours per entry
      - entries cannot overlap
      - employee must have Attendance.clock_in for today
      - if Attendance.clock_out exists: every entry.end_time <= attendance.clock_out
      - otherwise entries.end_time <= now (no future)
      - entry.start_time >= attendance.clock_in
    """
    entries = TimesheetEntryItemSerializer(many=True)

    def validate(self, data):
        entries = data.get("entries", [])
        if not entries:
            raise ValidationError("Entries list cannot be empty.")

        # today's date according to timezone
        today = timezone.localdate()

        # request & user context (serializer called with context={"request": request})
        request = self.context.get("request")
        if not request or not getattr(request, "user", None) or not request.user.is_authenticated:
            raise ValidationError("Request and authenticated user must be provided in serializer context.")

        user = request.user

        # get today's attendance for the user
        attendance = Attendance.objects.filter(user=user, date=today).first()
        if not attendance or not attendance.clock_in:
            raise ValidationError("You must clock in (attendance) before updating today's timesheet.")

        login_dt = attendance.clock_in
        now = timezone.now()

        # if attendance.clock_out exists, that becomes the cutoff; otherwise cutoff is now
        cutoff_dt = attendance.clock_out or now

        # validate each entry and collect intervals
        intervals = []
        for idx, it in enumerate(entries, start=1):
            s = it["start_time"]
            e = it["end_time"]

            # must be same day (today)
            if s.date() != today or e.date() != today:
                raise ValidationError({"entries": f"Entry #{idx} must be for today's date only."})

            # end must be after start
            if e <= s:
                raise ValidationError({"entries": f"Entry #{idx} end_time must be after start_time."})

            # max single-entry duration (6 hours)
            if (e - s).total_seconds() > 6 * 3600:
                raise ValidationError({"entries": f"Entry #{idx} cannot exceed 6 hours."})

            # cannot start before attendance clock_in
            if s < login_dt:
                raise ValidationError({"entries": f"Entry #{idx} starts before your attendance clock-in ({login_dt})."})

            # cannot end after cutoff (attendance.clock_out if set; otherwise now)
            if e > cutoff_dt:
                if attendance.clock_out:
                    # allow updating after clock_out but entries must not exceed clock_out
                    raise ValidationError({"entries": f"Entry #{idx} ends after attendance clock-out ({attendance.clock_out})."})
                else:
                    raise ValidationError({"entries": f"Entry #{idx} end_time cannot be in the future."})

            intervals.append((s, e))

        # check for overlapping intervals within submitted entries
        intervals_sorted = sorted(intervals, key=lambda x: x[0])
        for i in range(1, len(intervals_sorted)):
            if intervals_sorted[i][0] < intervals_sorted[i-1][1]:
                raise ValidationError("Submitted time entries cannot overlap each other.")

        return data

