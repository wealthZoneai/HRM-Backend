# hr/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from emp.models import EmployeeProfile, Shift, Attendance, CalendarEvent, SalaryStructure, EmployeeSalary, Payslip, LeaveRequest, LeaveType, LeaveBalance
from .models import Announcement
from django.utils import timezone
from datetime import datetime
from decimal import Decimal
from login.models import User

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'role')


class EmployeeListSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)

    class Meta:
        model = EmployeeProfile
        fields = ('id', 'emp_id', 'user', 'first_name', 'last_name', 'work_email',
                  'job_title', 'department', 'role', 'start_date', 'location', 'profile_photo')


class EmployeeHRContactUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeProfile
        fields = (
            "first_name",
            "middle_name",
            "last_name",
            "personal_email",
            "phone_number",
            "alternate_number",
            "dob",
            "blood_group",
            "gender",
            "marital_status",
        )


class EmployeeHRRoleUpdateSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(
        choices=[
            (User.ROLE_EMPLOYEE, "Employee"),
            (User.ROLE_INTERN, "Intern"),
            (User.ROLE_TL, "Team Lead"),
            (User.ROLE_HR, "HR"),
            (User.ROLE_MANAGEMENT, "Management"),
        ]

    )

    class Meta:
        model = EmployeeProfile
        fields = ("role",)

    def update(self, instance, validated_data):
        new_role = validated_data["role"]

        instance.role = new_role
        instance.user.role = new_role
        instance.user.save(update_fields=["role"])

        instance.save(update_fields=["role"])
        return instance


class EmployeeDetailSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)

    class Meta:
        model = EmployeeProfile
        fields = (
            "id",
            "emp_id",
            "user",
            "first_name",
            "middle_name",
            "last_name",
            "personal_email",
            "work_email",
            "phone_number",
            "alternate_number",
            "dob",
            "gender",
            "marital_status",
            "blood_group",
            "job_title",
            "department",
            "employment_type",
            "start_date",
            "location",
            "team_lead",
            "is_active",
            "profile_photo",
            "created_at",
        )


class FlexibleTeamLeadField(serializers.PrimaryKeyRelatedField):
    def to_internal_value(self, data):

        if isinstance(data, int) or (isinstance(data, str) and data.isdigit()):
            return super().to_internal_value(int(data))

        User = get_user_model()
        u = User.objects.filter(username__iexact=data).first(
        ) or User.objects.filter(email__iexact=data).first()
        if u:
            return u
        self.fail('does_not_exist', pk_value=data)


class EmployeeJobBankUpdateSerializer(serializers.ModelSerializer):
    team_lead = FlexibleTeamLeadField(queryset=User.objects.filter(
        role=User.ROLE_TL), required=False, allow_null=True)

    class Meta:
        model = EmployeeProfile
        fields = ('job_title', 'department', 'team_lead', 'employment_type', 'start_date', 'location', 'job_description',
                  'bank_name', 'account_number', 'ifsc_code', 'branch')


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = (
            "id",
            "name",
            "start_time",
            "end_time",
            "grace_minutes",
            "is_active",
        )


class AttendanceAdminSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    department = serializers.CharField(
        source="user.employeeprofile.department",
        read_only=True
    )

    class Meta:
        model = Attendance
        fields = (
            "id",
            "user",
            "department",
            "date",
            "clock_in",
            "clock_out",
            "status",
            "worked_seconds",
            "overtime_seconds",
            "late_arrivals",
            "manual_entry",
            "note",
        )


class CalendarEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = (
            "id",
            "title",
            "description",
            "event_type",
            "date",
            "start_time",
            "end_time",
            "created_by",
            "extra",
        )


class SalaryStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryStructure
        fields = (
            "id",
            "name",
            "monthly_ctc",
            "basic_percent",
            "hra_percent",
            "other_allowances",
            "overtime_multiplier",
        )


class EmployeeSalaryAdminSerializer(serializers.ModelSerializer):
    profile = EmployeeListSerializer(read_only=True)

    class Meta:
        model = EmployeeSalary
        fields = (
            "id",
            "profile",
            "structure",
            "effective_from",
            "is_active",
        )


class PayslipAdminSerializer(serializers.ModelSerializer):
    profile = EmployeeListSerializer(read_only=True)

    class Meta:
        model = Payslip
        fields = (
            "id",
            "profile",
            "year",
            "month",
            "working_days",
            "days_present",
            "gross_amount",
            "overtime_amount",
            "deductions",
            "net_amount",
            "finalized",
            "generated_at",
        )


class MySalaryDetailSerializer(serializers.ModelSerializer):
    basic = serializers.SerializerMethodField()
    hra = serializers.SerializerMethodField()
    pf = serializers.SerializerMethodField()
    gross = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeSalary
        fields = [
            "basic",
            "hra",
            "pf",
            "gross",
            "effective_from",
        ]

    def get_basic(self, obj):
        monthly_ctc = Decimal(obj.structure.monthly_ctc)
        return monthly_ctc * Decimal(obj.structure.basic_percent) / 100

    def get_hra(self, obj):
        monthly_ctc = Decimal(obj.structure.monthly_ctc)
        return monthly_ctc * Decimal(obj.structure.hra_percent) / 100

    def get_pf(self, obj):
        basic = self.get_basic(obj)
        return basic * Decimal("0.50")

    def get_gross(self, obj):
        return Decimal(obj.structure.monthly_ctc)


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'


class LeaveBalanceSerializer(serializers.ModelSerializer):
    profile = EmployeeListSerializer(read_only=True)

    class Meta:
        model = LeaveBalance
        fields = (
            "id",
            "profile",
            "leave_type",
            "total_allocated",
            "used",
        )


class LeaveRequestAdminSerializer(serializers.ModelSerializer):
    profile = EmployeeListSerializer(read_only=True)

    class Meta:
        model = LeaveRequest
        fields = (
            "id",
            "profile",
            "leave_type",
            "start_date",
            "end_date",
            "days",
            "status",
            "reason",
            "applied_on",
            "tl",
            "hr",
        )


class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = '__all__'
        read_only_fields = ('created_by',)

    def to_internal_value(self, data):
        if 'priority' in data and isinstance(data['priority'], str):
            data['priority'] = data['priority'].upper()
        if 'audience' in data and isinstance(data['audience'], str):
            data['audience'] = data['audience'].upper()
        return super().to_internal_value(data)

    def validate(self, attrs):
        date = attrs.get('date')
        time = attrs.get('time')

        if self.instance:
            pass
        else:
            # ✅ 1. Prevent past date
            today = timezone.localdate()
            if date < today:
                raise serializers.ValidationError(
                    "Past dates are not allowed."
                )

            # ✅ 2. Prevent past time for today
            if date == today:
                current_time = timezone.localtime().time()
                if time <= current_time:
                    raise serializers.ValidationError(
                        "Past time is not allowed for today's date."
                    )

        # ✅ 3. Prevent duplicate date + time
        qs = Announcement.objects.filter(date=date, time=time)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "An announcement already exists at this date and time."
            )
        return attrs
