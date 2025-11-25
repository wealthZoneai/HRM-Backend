from emp.models import EmployeeProfile
from rest_framework import serializers
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import EmployeeProfile, Attendance
from django.utils import timezone
from django.contrib.auth.hashers import make_password


User = get_user_model()


class EmployeeReadSerializer(serializers.ModelSerializer):
    # show some user-level fields alongside profile
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    # profile.role or mirrored user role
    role = serializers.CharField(read_only=True)

    class Meta:
        model = EmployeeProfile
        # Explicit fields for clarity (instead of '__all__')
        fields = [
            'id', 'username', 'email', 'role',
            'emp_id', 'first_name', 'last_name', 'dob', 'gender',
            'work_email', 'personal_email', 'phone_number',
            'job_title', 'department', 'manager', 'employment_type', 'start_date', 'location', 'job_description',
            'bank_name', 'account_number', 'ifsc_code', 'branch',
            'aadhaar', 'pan', 'id_card',
            'passport_image', 'id_card_image', 'aadhaar_image', 'pan_image',
            'profile_photo',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields  # list API and read API are read-only

# Serializer used by HR/Management to create an employee


User = get_user_model()


class EmployeeCreateByHRSerializer(serializers.Serializer):

    # HR inputs
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    role = serializers.CharField()

    job_title = serializers.CharField(required=False)
    department = serializers.CharField(required=False)
    employment_type = serializers.CharField(required=False)
    start_date = serializers.DateField(required=False)
    location = serializers.CharField(required=False)

    manager = serializers.IntegerField(required=False)

    # Auto-generated fields (read-only)
    username = serializers.CharField(read_only=True)
    work_email = serializers.EmailField(read_only=True)

    def validate_role(self, value):
        allowed = ["employee", "intern", "tl"]
        if value not in allowed:
            raise serializers.ValidationError("Invalid role.")
        return value

    def create(self, validated_data):
        first_name = validated_data["first_name"]
        last_name = validated_data["last_name"]
        role = validated_data["role"]

        # Create user using create_user so Django fields set properly
        # Use an empty password first, then mark unusable.
        user = User.objects.create_user(
            username="",   # signal will generate username
            password=None,  # create_user allows None, but we'll set unusable below
            first_name=first_name,
            last_name=last_name,
            role=role,
            email=""       # signal will generate/fill email if needed
        )

        # Immediately make password unusable so login fails until reset
        user.set_unusable_password()
        user.save(update_fields=['password'])

        # Signal will auto-create EmployeeProfile (login/signals.py)
        profile = user.employeeprofile

        # Fill profile fields provided by HR
        for field in ["emp_id", "job_title", "department", "employment_type",
                      "start_date", "location"]:
            if field in validated_data:
                setattr(profile, field, validated_data[field])

        if "manager" in validated_data:
            try:
                profile.manager = User.objects.get(
                    id=validated_data["manager"])
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {"manager": "Manager user does not exist."})

        profile.save()
        return profile


class EmployeeUpdateByEmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeProfile
        fields = [
            'personal_email',
            'phone_number',
            'profile_photo',
            'passport_image',
            'id_card_image',
            'aadhaar_image',
            'pan_image',
        ]


class AttendanceReadSerializer(serializers.ModelSerializer):
    # friendly formatted fields
    clock_in_iso = serializers.DateTimeField(source='clock_in', read_only=True)
    clock_out_iso = serializers.DateTimeField(
        source='clock_out', read_only=True)
    duration_seconds = serializers.IntegerField(read_only=True)
    duration_human = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = [
            'id', 'user', 'date', 'clock_in_iso', 'clock_out_iso',
            'duration_seconds', 'duration_human', 'status', 'note',
        ]
        read_only_fields = fields

    def get_duration_human(self, obj):
        if not obj.duration_seconds:
            return None
        secs = obj.duration_seconds
        hours = secs // 3600
        mins = (secs % 3600) // 60
        secs_rem = secs % 60
        return f"{hours}h {mins}m {secs_rem}s"


class ClockInSerializer(serializers.Serializer):
    # optional note
    note = serializers.CharField(
        required=False, allow_blank=True, allow_null=True)

    def validate(self, data):
        # nothing complex here; controller (view) will enforce one-per-day
        return data


class ClockOutSerializer(serializers.Serializer):
    # optional note on clock-out
    note = serializers.CharField(
        required=False, allow_blank=True, allow_null=True)

    def validate(self, data):
        return data
