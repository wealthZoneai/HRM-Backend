# tl/serializers.py
from .models import TLAnnouncement
from rest_framework import serializers
from emp.models import EmployeeProfile
from hr.serializers import UserBasicSerializer
from django.utils import timezone
from datetime import timedelta, datetime


class TeamMemberSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)

    class Meta:
        model = EmployeeProfile
        fields = ("id", "user", "emp_id", "first_name", "last_name",
                  "work_email", "job_title", "department", "profile_photo")


class TLAnnouncementSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = TLAnnouncement
        fields = "__all__"
        read_only_fields = ("created_by", "created_role", "id")

    def validate(self, attrs):
        date = attrs.get('date')
        time = attrs.get('time')
        today = timezone.localdate()
        if date < today:
            raise serializers.ValidationError("Past dates are not allowed.")
        if date == today:
            current_time = timezone.localtime().time()
            if time <= current_time:
                raise serializers.ValidationError(
                    "Past time is not allowed for today's date.")
        if TLAnnouncement.objects.filter(date=date, time=time).exists():
            raise serializers.ValidationError(
                "An announcement already exists at this date and time.")
        return attrs
