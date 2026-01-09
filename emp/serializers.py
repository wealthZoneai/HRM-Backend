# emp/serializers.py
from django.core.exceptions import ValidationError
from urllib3 import request
from .models import TimesheetEntry, TimesheetDay, Attendance
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import (
    EmployeeProfile, Notification, Shift, Attendance, CalendarEvent,
    SalaryStructure, EmployeeSalary, Payslip,
    LeaveType, LeaveBalance, LeaveRequest, Policy
)
import re
import unicodedata
from django.contrib.auth import get_user_model
from datetime import datetime
from django.utils import timezone
from django.urls import reverse
from .constants import LEAVE_TYPE_CHOICES, EMPLOYEE_DEPARTMENT_CHOICES
from decimal import Decimal

User = get_user_model()

today = timezone.localdate()


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
    department = serializers.ChoiceField(
        choices=EMPLOYEE_DEPARTMENT_CHOICES,
        required=True
    )
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
        required=False, allow_blank=True, max_length=12)
    aadhaar_image = serializers.ImageField(required=False, allow_null=True)
    pan_number = serializers.CharField(
        required=False, allow_blank=True, max_length=20)
    pan_image = serializers.ImageField(required=False, allow_null=True)
    passport_number = serializers.CharField(
        required=False, allow_blank=True, max_length=20)
    passport_image = serializers.ImageField(required=False, allow_null=True)


class EmployeeCreateSerializer(serializers.Serializer):

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

    contact = ContactSerializer(required=True)
    job = JobSerializer(required=True)
    bank = BankSerializer(required=False)
    identification = IdentificationSerializer(required=False)

    def _normalize_name(self, value: str) -> str:
        if not value:
            return ""
        value = unicodedata.normalize("NFKD", value)
        value = value.encode("ascii", "ignore").decode("ascii")
        value = re.sub(r"\s+", " ", value)
        return value.strip()

    def _username_part(self, value: str) -> str:
        value = value.replace(" ", "").lower()
        value = re.sub(r"[^a-z0-9]", "", value)
        return value

    def validate_work_email(self, value):
        if value:
            value = re.sub(r"\s+", "", value)
            if User.objects.filter(email__iexact=value).exists():
                raise serializers.ValidationError(
                    "User with this email already exists."
                )
        return value

    def validate(self, data):
        job = data.get('job', {}) or {}
        tl_val = job.get('team_lead')

        if not tl_val:
            return data

        if str(tl_val).isdigit():
            user = User.objects.filter(id=int(tl_val)).first()
        else:
            user = (
                User.objects.filter(username__iexact=tl_val).first()
                or User.objects.filter(email__iexact=tl_val).first()
            )

        if not user:
            raise ValidationError({
                "job": {
                    "team_lead": "Invalid team_lead: user not found."
                }
            })

        if user.role != 'tl':
            raise ValidationError({
                "job": {
                    "team_lead": f"Invalid selection: '{user.username}' is not a Team Lead."
                }
            })

        data.setdefault('job', {})['team_lead'] = user.id
        return data

    def create(self, validated_data):
        contact = validated_data.get('contact', {})
        job = validated_data.get('job', {})
        bank = validated_data.get('bank', {})
        identification = validated_data.get('identification', {})

        first_name = self._normalize_name(contact.get('first_name'))
        last_name = self._normalize_name(contact.get('last_name'))

        username_first = self._username_part(first_name)
        username_last = self._username_part(last_name)

        base_username = ".".join(filter(None, [username_first, username_last]))
        base_username = base_username.strip(".") or "user"

        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        raw_email = validated_data.get('work_email')

        if raw_email:
            # If HR provided email, clean it
            email = re.sub(r"\s+", "", raw_email)
        else:
            # Auto-generate email from sanitized username parts
            email_local = ".".join(
                filter(None, [username_first, username_last]))
            email_local = email_local.strip(".") or "user"
            email = f"{email_local}@wealthzonegroupai.com"

        role = validated_data.get('role', 'employee')

        user = User.objects.create_user(
            username=username,
            password=None,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=role
        )
        user.set_unusable_password()
        user.save(update_fields=["password"])

        prof, created = EmployeeProfile.objects.get_or_create(
            user=user,
            defaults={
                'emp_id': validated_data.get('emp_id') or '',
                'work_email': email or '',
                'first_name': first_name,
                'last_name': last_name,
            }
        )

        if prof.role != role:
            prof.role = role

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

        prof.job_title = job.get('job_title') or prof.job_title
        prof.department = job.get('department') or prof.department
        prof.employment_type = job.get(
            'employment_type') or prof.employment_type
        prof.start_date = job.get('start_date') or prof.start_date
        prof.location = job.get('location') or prof.location
        prof.job_description = job.get(
            'job_description') or prof.job_description

        if job.get('team_lead'):
            prof.team_lead_id = int(job.get('team_lead'))

        if job.get('id_image') is not None:
            prof.id_image = job.get('id_image')

        if bank:
            prof.bank_name = bank.get('bank_name') or prof.bank_name
            prof.ifsc_code = bank.get('ifsc_code') or prof.ifsc_code
            prof.account_number = bank.get(
                'account_number') or prof.account_number
            prof.branch = bank.get('branch') or prof.branch

        if identification:
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

        if email:
            prof.work_email = email

        prof.save()

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
        if not obj.profile_photo:
            return None
        request = self.context.get("request", None)
        try:
            url = reverse("protected_employee_media",
                          args=[obj.pk, "profile_photo"])
        except Exception:
            return None
        if request:
            return request.build_absolute_uri(url)

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
        if not obj.id_image:
            return None
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
    """
    Employee can update ONLY EMPTY contact fields.
    HR / Management can update anytime.
    """

    class Meta:
        model = EmployeeProfile
        fields = (
            'personal_email',
            'phone_number',
            'alternate_number',
            'dob',
            'blood_group',
            'gender',
            'marital_status',
            'profile_photo',
        )

    def validate(self, data):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if not user:
            return data

        role = (getattr(user, "role", "") or "").lower()
        is_hr = role in ("hr", "management")

        # HR can update freely
        if is_hr:
            return data

        # Employee: allow ONLY empty fields
        instance = self.instance
        errors = {}

        for field, value in data.items():

            if field == 'profile_photo':
                continue

            existing_value = getattr(instance, field, None)

            if existing_value not in (None, "", []):
                errors[field] = "This field can only be modified by HR."

        if errors:
            raise serializers.ValidationError(errors)

        return data


class EmployeeProfileImageUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeProfile
        fields = ('profile_photo')


class EmployeeIdentificationSerializer(serializers.ModelSerializer):
    """
    Employee can upload identification ONLY if EMPTY.
    HR / Management can update anytime.
    """

    def validate_aadhaar_number(self, value):
        if not value:
            return value  # allow blank / optional

        value = value.replace(" ", "")
        if not re.fullmatch(r"\d{12}", value):
            raise serializers.ValidationError(
                "Aadhaar number must be exactly 12 digits."
            )
        return value

    def validate_pan(self, value):
        if not value:
            return value  # allow blank / optional

        value = value.replace(" ", "").upper()
        if not re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]{1}", value):
            raise serializers.ValidationError(
                "PAN must be in format ABCDE1234F (uppercase)."
            )
        return value

    def validate_passport_number(self, value):
        if not value:
            return value

        value = value.replace(" ", "").upper()
        if not re.fullmatch(r"[A-Z][0-9]{7}", value):
            raise serializers.ValidationError(
                "Passport number must be 1 uppercase letter followed by 7 digits (e.g. A1234567)."
            )
        return value

    class Meta:
        model = EmployeeProfile
        fields = (
            'aadhaar_number',
            'aadhaar_front_image',
            'aadhaar_back_image',

            'pan',
            'pan_front_image',
            'pan_back_image',

            'passport_number',
            'passport_front_image',
            'passport_back_image',
        )

    def validate(self, data):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if not user:
            return data

        role = (getattr(user, "role", "") or "").lower()
        is_hr = role in ("hr", "management")

        if is_hr:
            return data

        instance = self.instance
        errors = {}

        for field, value in data.items():
            existing_value = getattr(instance, field, None)

            if existing_value not in (None, "", []):
                errors[field] = "This identification field can only be modified by HR."

        if errors:
            raise serializers.ValidationError(errors)

        return data


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'title', 'body', 'notif_type',
                  'is_read', 'created_at', 'extra')


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = '__all__'


class AttendanceReadSerializer(serializers.ModelSerializer):
    total_hours = serializers.SerializerMethodField()
    overtime = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = '__all__'

    def format_time(self, duration):
        if not duration:
            return "0h 0m"
        seconds = duration.total_seconds()
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m}m"

    def get_total_hours(self, obj):
        return self.format_time(obj.total_hours)

    def get_overtime(self, obj):
        return self.format_time(obj.overtime)


class TodayAttendanceSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)

    class Meta:
        model = Attendance
        fields = [
            "user_id",
            "user_name",
            "date",
            "clock_in",
            "clock_out",
            "duration_time",
            "status",
        ]


class CalendarEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at']


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
    leave_type = serializers.CharField(max_length=20)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    reason = serializers.CharField(
        required=True, allow_blank=False, max_length=500)

    def validate(self, data):
        today = timezone.localdate()
        start = data["start_date"]
        end = data["end_date"]

        # ❌ Past dates not allowed
        if start < today:
            raise serializers.ValidationError(
                {"start_date": "Start date cannot be in the past."}
            )

        if end < start:
            raise serializers.ValidationError(
                {"end_date": "End date cannot be before start date."}
            )

        requested_days = (end - start).days + 1

        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return data

        profile = getattr(request.user, "employeeprofile", None)
        if not profile:
            raise serializers.ValidationError(
                "Employee profile not found for current user."
            )

        # ❌ Overlapping leave check
        overlapping = LeaveRequest.objects.filter(
            profile=profile
        ).exclude(
            status__in=["tl_rejected", "hr_rejected"]
        ).filter(
            start_date__lte=end,
            end_date__gte=start
        ).exists()

        if overlapping:
            raise serializers.ValidationError(
                {"non_field_errors": "You already have a leave request that overlaps these dates."}
            )

        # ✅ Validate leave type (ENUM)
        valid_leave_types = [c[0] for c in LEAVE_TYPE_CHOICES]
        leave_type = data["leave_type"]

        if leave_type not in valid_leave_types:
            raise serializers.ValidationError(
                {"leave_type": "Invalid leave type."}
            )

        # ✅ Leave balance check (ENUM-based)
        lb = LeaveBalance.objects.filter(
            profile=profile,
            leave_type=leave_type
        ).first()

        if lb:
            try:
                available = Decimal(lb.total_allocated) - Decimal(lb.used)
            except Exception:
                available = None

            if available is not None and Decimal(requested_days) > available:
                label = dict(LEAVE_TYPE_CHOICES).get(leave_type, leave_type)
                raise serializers.ValidationError(
                    {
                        "non_field_errors": (
                            f"Insufficient leave balance for '{label}'. "
                            f"Requested: {requested_days}, Available: {available}."
                        )
                    }
                )

        # ✅ Store computed values
        data["calculated_days"] = requested_days
        data["normalized_leave_type"] = leave_type

        return data


class PolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = Policy
        fields = '__all__'


class TimesheetEntrySerializer(serializers.ModelSerializer):
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()
    duration_hours = serializers.SerializerMethodField()
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
        read_only_fields = [
            "duration_seconds",
            "duration_hours",
            "created_at",
            "updated_at",
        ]

    # 🔒 SAFE duration handling (unchanged)
    def _get_total_seconds_safe(self, obj):
        try:
            return int(obj.duration_seconds) if obj.duration_seconds is not None else 0
        except (TypeError, ValueError):
            return 0

    def get_duration_hours(self, obj):
        total = self._get_total_seconds_safe(obj)
        return round(total / 3600.0, 2)

    def get_duration_seconds(self, obj):
        total = self._get_total_seconds_safe(obj)
        h = total // 3600
        m = (total % 3600) // 60
        s = total % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    # ✅ THIS IS THE MISSING PIECE (CRITICAL)
    def get_start_time(self, obj):
        return timezone.localtime(obj.start_time) if obj.start_time else None

    def get_end_time(self, obj):
        return timezone.localtime(obj.end_time) if obj.end_time else None

    def validate_project_task(self, task):
        request = self.context.get('request')
        if task and task.assigned_to != request.user:
            raise serializers.ValidationError(
                "You can log time only for your own task."
            )
        return task


class TimesheetDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = TimesheetDay
        fields = ("date", "clock_in", "clock_out", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")


class TimesheetEntryItemSerializer(serializers.Serializer):
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    task = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)


class DailyTimesheetUpdateSerializer(serializers.Serializer):
    date = serializers.DateField()
    entries = TimesheetEntryItemSerializer(many=True)

    def validate(self, data):
        request = self.context.get("request")
        user = request.user
        prof = user.employeeprofile

        date = data["date"]
        entries = data["entries"]

        if not entries:
            raise ValidationError("Entries cannot be empty.")

        if date > timezone.localdate():
            raise ValidationError("Future dates are not allowed.")

        attendance = Attendance.objects.filter(user=user, date=date).first()
        if not attendance or not attendance.clock_in:
            raise ValidationError("Attendance clock-in is required.")

        ts_day, _ = TimesheetDay.objects.get_or_create(
            profile=prof,
            date=date,
            defaults={"attendance": attendance}
        )

        if ts_day.is_submitted:
            raise ValidationError("Timesheet already submitted and locked.")

        login_dt = attendance.clock_in
        logout_dt = attendance.clock_out

        intervals = []

        for idx, e in enumerate(entries, start=1):
            s = e["start_time"]
            en = e["end_time"]

            if s >= en:
                raise ValidationError(
                    f"Entry #{idx}: end_time must be after start_time.")

            s_dt = timezone.make_aware(datetime.combine(date, s))
            e_dt = timezone.make_aware(datetime.combine(date, en))

            if s_dt < login_dt:
                raise ValidationError(f"Entry #{idx}: starts before clock-in.")

            if logout_dt and e_dt > logout_dt:
                raise ValidationError(f"Entry #{idx}: ends after clock-out.")

            if not logout_dt and e_dt > timezone.now():
                raise ValidationError(
                    f"Entry #{idx}: future time not allowed.")

            if (e_dt - s_dt).total_seconds() > 6 * 3600:
                raise ValidationError(f"Entry #{idx}: exceeds 6 hours.")

            intervals.append((s_dt, e_dt))

        intervals.sort()
        for i in range(1, len(intervals)):
            if intervals[i][0] < intervals[i - 1][1]:
                raise ValidationError("Time entries overlap.")

        data["attendance"] = attendance
        return data


class EmployeeSensitiveSelfSerializer(serializers.ModelSerializer):
    """
    Full sensitive data for the OWNER only.
    This serializer MUST NOT be used in list or profile APIs.
    """

    aadhaar_front_image_url = serializers.SerializerMethodField()
    aadhaar_back_image_url = serializers.SerializerMethodField()

    pan_front_image_url = serializers.SerializerMethodField()
    pan_back_image_url = serializers.SerializerMethodField()

    passport_front_image_url = serializers.SerializerMethodField()
    passport_back_image_url = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeProfile
        fields = (
            "aadhaar_number",

            "aadhaar_front_image_url",
            "aadhaar_back_image_url",

            "pan",
            "pan_front_image_url",
            "pan_back_image_url",

            "passport_number",
            "passport_front_image_url",
            "passport_back_image_url",

            "bank_name",
            "ifsc_code",
            "account_number",
            "branch",
        )

    def _build_url(self, obj, field_name):
        request = self.context.get("request")
        if not request:
            return None

        if not getattr(obj, field_name):
            return None

        url = reverse(
            "protected_employee_document",
            args=[obj.emp_id, field_name]
        )

        return request.build_absolute_uri(url)

    def get_aadhaar_front_image_url(self, obj):
        return self._build_url(obj, "aadhaar_front_image")

    def get_aadhaar_back_image_url(self, obj):
        return self._build_url(obj, "aadhaar_back_image")

    def get_pan_front_image_url(self, obj):
        return self._build_url(obj, "pan_front_image")

    def get_pan_back_image_url(self, obj):
        return self._build_url(obj, "pan_back_image")

    def get_passport_front_image_url(self, obj):
        return self._build_url(obj, "passport_front_image")

    def get_passport_back_image_url(self, obj):
        return self._build_url(obj, "passport_back_image")


class EmployeeSensitiveHRSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    aadhaar_front_image_url = serializers.SerializerMethodField()
    aadhaar_back_image_url = serializers.SerializerMethodField()

    pan_front_image_url = serializers.SerializerMethodField()
    pan_back_image_url = serializers.SerializerMethodField()

    passport_front_image_url = serializers.SerializerMethodField()
    passport_back_image_url = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeProfile
        fields = (
            "user",
            "emp_id",
            "first_name",
            "last_name",

            "aadhaar_number",
            "aadhaar_front_image_url",
            "aadhaar_back_image_url",

            "pan",
            "pan_front_image_url",
            "pan_back_image_url",

            "passport_number",
            "passport_front_image_url",
            "passport_back_image_url",

            "bank_name",
            "ifsc_code",
            "account_number",
            "branch",
        )

    def _build_url(self, obj, field_name):
        request = self.context.get("request")
        file = getattr(obj, field_name, None)

        if not file:
            return None

        if request:
            return request.build_absolute_uri(file.url)

        return file.url

    def get_aadhaar_front_image_url(self, obj):
        return self._build_url(obj, "aadhaar_front_image")

    def get_aadhaar_back_image_url(self, obj):
        return self._build_url(obj, "aadhaar_back_image")

    def get_pan_front_image_url(self, obj):
        return self._build_url(obj, "pan_front_image")

    def get_pan_back_image_url(self, obj):
        return self._build_url(obj, "pan_back_image")

    def get_passport_front_image_url(self, obj):
        return self._build_url(obj, "passport_front_image")

    def get_passport_back_image_url(self, obj):
        return self._build_url(obj, "passport_back_image")

    def get_user(self, obj):
        return {
            "id": obj.user.id,
            "username": obj.user.username,
            "email": obj.user.email,
            "role": obj.user.role,
        }
