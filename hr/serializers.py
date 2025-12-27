# hr/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from emp.models import EmployeeProfile, Shift, Attendance, CalendarEvent, SalaryStructure, EmployeeSalary, Payslip, LeaveRequest, LeaveType, LeaveBalance
from .models import Announcement
from .models import TLAnnouncement as HR_TLAnnouncement
from django.utils import timezone
from datetime import datetime
from decimal import Decimal

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
            ("employee", "Employee"),
            ("intern", "Intern"),
            ("tl", "Team Lead"),
            ("hr", "HR"),
            ("management", "Management"),
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
        fields = '__all__'
        read_only_fields = ('emp_id', 'work_email',
                            'username', 'created_at', 'user')


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
        role='tl'), required=False, allow_null=True)

    class Meta:
        model = EmployeeProfile
        fields = ('job_title', 'department', 'team_lead', 'employment_type', 'start_date', 'location', 'job_description',
                  'bank_name', 'account_number', 'ifsc_code', 'branch')


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = '__all__'


class AttendanceAdminSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)

    class Meta:
        model = Attendance
        fields = '__all__'


class CalendarEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = '__all__'


class SalaryStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryStructure
        fields = '__all__'


class EmployeeSalaryAdminSerializer(serializers.ModelSerializer):
    profile = EmployeeListSerializer(read_only=True)

    class Meta:
        model = EmployeeSalary
        fields = '__all__'


class PayslipAdminSerializer(serializers.ModelSerializer):
    profile = EmployeeListSerializer(read_only=True)

    class Meta:
        model = Payslip
        fields = '__all__'


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
        fields = '__all__'


class LeaveRequestAdminSerializer(serializers.ModelSerializer):
    profile = EmployeeListSerializer(read_only=True)

    class Meta:
        model = LeaveRequest
        fields = '__all__'


class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = '__all__'
        read_only_fields = ('created_by',)

    def to_internal_value(self, data):
        if 'priority' in data and isinstance(data['priority'], str):
            data['priority'] = data['priority'].upper()
        if 'department' in data and isinstance(data['department'], str):
            data['department'] = data['department'].upper()
        return super().to_internal_value(data)

    def validate(self, attrs):
        date = attrs.get('date')
        time = attrs.get('time')

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
        if Announcement.objects.filter(date=date, time=time).exists():
            raise serializers.ValidationError(
                "An announcement already exists at this date and time."
            )
        return attrs


class TLAnnouncementSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = HR_TLAnnouncement
        fields = "__all__"
        read_only_fields = ("created_by", "created_at", "id")
