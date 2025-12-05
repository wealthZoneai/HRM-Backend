# emp/serializers.py
from rest_framework import serializers

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
        'full_time', 'Full Time'), ('contract', 'Contract'), ('intern', 'Intern')], required=True)
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
    role = serializers.ChoiceField(choices=[('employee', 'Employee'), ('intern', 'Intern'), (
        'tl', 'Team Leader'), ('hr', 'HR'), ('management', 'Management')], default='employee')
    emp_id = serializers.CharField(
        required=False, allow_blank=True, max_length=50)
    work_email = serializers.EmailField(required=False, allow_blank=True)

    # nested sections (required/optional as per your spec)
    contact = ContactSerializer(required=True)
    job = JobSerializer(required=True)
    bank = BankSerializer(required=True)
    identification = IdentificationSerializer(required=False)

    def validate_work_email(self, value):
        if value and User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "User with this email already exists.")
        return value

    def create(self, validated_data):
        # extract nested parts
        contact = validated_data.get('contact', {})
        job = validated_data.get('job', {})
        bank = validated_data.get('bank', {})
        identification = validated_data.get('identification', {})

        first_name = (contact.get('first_name') or '').strip()
        last_name = (contact.get('last_name') or '').strip()
        role = validated_data.get('role', 'employee')
        email = (validated_data.get('work_email') or '').strip() or None

        # username generation (same approach as your existing create_user flow)
        base_username = f"{first_name.lower()}.{last_name.lower()}" if first_name or last_name else "user"
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username, password=None, first_name=first_name, last_name=last_name, email=email, role=role
        )
        user.set_unusable_password()
        user.save()

        # ensure EmployeeProfile exists via signals (but update with provided fields)
        prof, created = EmployeeProfile.objects.get_or_create(user=user, defaults={
            'emp_id': validated_data.get('emp_id') or '',
            'work_email': email or '',
            'first_name': first_name or '',
            'last_name': last_name or '',
            'role': role
        })

        # update emp_id if provided
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
        # profile_photo may be an InMemoryUploadedFile
        if contact.get('profile_photo') is not None:
            prof.profile_photo = contact.get('profile_photo')

        # JOB
        prof.job_title = job.get('job_title') or prof.job_title
        prof.department = job.get('department')
        tl_val = job.get('team_lead')
        if tl_val:
            # If numeric, keep old behavior (backwards compatibility)
            try:
                if str(tl_val).isdigit():
                    prof.team_lead_id = int(tl_val)
                else:
                    # Accept username or email (frontend should send username or email)
                    try:
                        # try username first
                        u = User.objects.get(username=tl_val)
                    except User.DoesNotExist:
                        # fallback to email lookup (case-insensitive)
                        u = User.objects.filter(email__iexact=tl_val).first()
                    if u:
                        prof.team_lead = u
            except Exception:
                # ignore invalid values (or log if you want)
                pass

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

        # work_email update if provided
        if email:
            prof.work_email = email

        # Save only changed fields for minimal impact
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
        # filter only existing fields on model to avoid errors
        valid_update_fields = [f for f in update_fields if hasattr(prof, f)]
        prof.save(update_fields=valid_update_fields)

        return user, prof

    def save(self, **kwargs):
        return self.create(self.validated_data)


class EmployeeProfileReadSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeProfile
        fields = (
            'user', 'emp_id', 'work_email', 'first_name', 'middle_name', 'last_name',
            'personal_email', 'phone_number', 'alternate_number', 'dob', 'blood_group',
            'gender', 'marital_status',
            'job_title', 'department', 'team_lead', 'employment_type', 'start_date',
            'location', 'job_description', 'id_image', 'profile_photo',
            'bank_name', 'ifsc_code', 'masked_account_number', 'branch',
            'masked_aadhaar', 'aadhaar_image', 'masked_pan', 'pan_image', 'masked_passport', 'passport_image',
            'role', 'created_at', 'updated_at'
        )
        read_only_fields = ('emp_id', 'work_email', 'user',
                            'created_at', 'updated_at')

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

    masked_aadhaar = serializers.SerializerMethodField()
    masked_pan = serializers.SerializerMethodField()
    masked_passport = serializers.SerializerMethodField()
    masked_account_number = serializers.SerializerMethodField()

    protected_profile_photo_url = serializers.SerializerMethodField()
    protected_aadhaar_image_url = serializers.SerializerMethodField()
    protected_pan_image_url = serializers.SerializerMethodField()
    protected_passport_image_url = serializers.SerializerMethodField()
    protected_id_image_url = serializers.SerializerMethodField()

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

    def get_user(self, obj):
        return {
            "id": obj.user.id,
            "username": obj.user.username,
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name,
            "email": obj.user.email,
            "role": obj.user.role,
        }


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
        fields = ('id', 'date', 'shift', 'clock_in', 'clock_out', 'duration_seconds', 'status',
                  'is_remote', 'late_by_seconds', 'overtime_seconds', 'note', 'manual_entry')


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
