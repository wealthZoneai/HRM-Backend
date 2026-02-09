# hr/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from emp.models import EmployeeProfile, Shift, Attendance, CalendarEvent, SalaryStructure, EmployeeSalary, Payslip, LeaveRequest, LeaveType, LeaveBalance
from django.contrib.auth import get_user_model
from .models import Announcement
from django.utils import timezone
from datetime import datetime
from decimal import Decimal

User = get_user_model()

# User-light serializer (for HR lists)
class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id','username','first_name','last_name','email','role')

# Employee list / detail
class EmployeeListSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    class Meta:
        model = EmployeeProfile
        fields = ('id','emp_id','user','first_name','last_name','work_email','job_title','department','role','start_date','location','profile_photo')

class EmployeeDetailSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    class Meta:
        model = EmployeeProfile
        fields = '__all__'
        read_only_fields = ('emp_id','work_email','username','created_at','user')

class FlexibleTeamLeadField(serializers.PrimaryKeyRelatedField):
    def to_internal_value(self, data):
        # accept int id
        if isinstance(data, int) or (isinstance(data, str) and data.isdigit()):
            return super().to_internal_value(int(data))
        # accept username or email
        User = get_user_model()
        u = User.objects.filter(username__iexact=data).first() or User.objects.filter(email__iexact=data).first()
        if u:
            return u
        self.fail('does_not_exist', pk_value=data)

class EmployeeJobBankUpdateSerializer(serializers.ModelSerializer):
    team_lead = FlexibleTeamLeadField(queryset=User.objects.filter(role='tl'), required=False, allow_null=True)
    class Meta:
        model = EmployeeProfile
        fields = ('job_title','department','team_lead','employment_type','start_date','location','job_description',
                  'bank_name','account_number','ifsc_code','branch')

# Shift & Attendance serializers (HR)
class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = '__all__'

class AttendanceAdminSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    class Meta:
        model = Attendance
        fields = '__all__'

# Calendar event (HR create)
class CalendarEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = '__all__'

# Salary and payslip admin serializers
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

# Leave admin serializers
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


        
from rest_framework import serializers
from .models import Announcement



class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = '__all__'  
        read_only_fields = ('created_by', 'date') 



# class TLAnnouncementSerializer(serializers.ModelSerializer):
#     created_by = serializers.PrimaryKeyRelatedField(read_only=True)

#     class Meta:
#         model = HR_TLAnnouncement
#         fields = "__all__"
#         read_only_fields = ("created_by", "created_at", "id")
class TLAnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = '__all__'
    
