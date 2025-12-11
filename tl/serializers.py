# tl/serializers.py
from rest_framework import serializers
from emp.models import EmployeeProfile, LeaveRequest, Attendance
from emp.serializers import LeaveRequestSerializer, AttendanceReadSerializer
from hr.serializers import UserBasicSerializer


class TeamMemberSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    class Meta:
        model = EmployeeProfile
        fields = ("id","user", "emp_id", "first_name", "last_name",
                  "work_email", "job_title", "department", "profile_photo")

from rest_framework import serializers
from .models import TLAnnouncement

class TLAnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = TLAnnouncement
        fields = "__all__"
    