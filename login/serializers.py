from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q
from django.core.exceptions import ValidationError
from .models import PasswordResetOTP
from .utils import generate_otp, send_otp_email
import re
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add role into JWT payload
        token["role"] = user.role
        token["username"] = user.username

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Add these fields in login response
        data["role"] = self.user.role.lower()  # force lowercase
        data["username"] = self.user.username

        return data


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def create(self, validated_data):
        input_email = validated_data["email"].lower()

        # Lookup user by checking both the base email AND the EmployeeProfile work_email
        user = User.objects.filter(
            Q(email__iexact=input_email) | Q(
                employeeprofile__work_email__iexact=input_email)
        ).first()

        if not user:
            return {"email": input_email}

        now = timezone.now()

        # --- Max 3 OTPs per hour limit ---
        one_hour_ago = now - timedelta(hours=1)
        recent_otps_count = PasswordResetOTP.objects.filter(
            user=user,
            created_at__gte=one_hour_ago
        ).count()

        if recent_otps_count >= 3:
            raise serializers.ValidationError({
                "email": "You have reached the maximum limit of 3 OTP requests per hour. Please try again later."
            })

        latest_otp = PasswordResetOTP.objects.filter(
            user=user).order_by('-created_at').first()

        if latest_otp:
            # OPTIMIZATION: Reused 'now' variable here
            time_passed = now - latest_otp.created_at
            if time_passed < timedelta(minutes=5):
                remaining_time = 5 - int(time_passed.total_seconds() // 60)
                raise serializers.ValidationError({
                    "email": f"Please wait at least {remaining_time} more minute(s) before requesting a new OTP."
                })

        otp = generate_otp()
        PasswordResetOTP.create_otp(user, otp)

        target_email = input_email
        if hasattr(user, 'employeeprofile') and user.employeeprofile.work_email:
            target_email = user.employeeprofile.work_email
        else:
            target_email = user.email

        send_otp_email(target_email, otp)

        return {"email": input_email}


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        # 1. Password Matching
        if data.get("new_password") != data.get("confirm_password"):
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })

        # 2. Password Complexity
        validate_password(data["new_password"])

        if not re.search(r"[A-Z]", data["new_password"]):
            raise serializers.ValidationError(
                "Password must contain uppercase letter")

        if not re.search(r"[a-z]", data["new_password"]):
            raise serializers.ValidationError(
                "Password must contain lowercase letter")

        if not re.search(r"[0-9]", data["new_password"]):
            raise serializers.ValidationError("Password must contain a number")

        if not re.search(r"[^A-Za-z0-9]", data["new_password"]):
            raise serializers.ValidationError(
                "Password must contain a special character")

        if len(data["new_password"]) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long")

        # 3. Secure OTP Validation
        email = data["email"].lower()
        otp = data["otp"]

        # Find the correct user (checking both base email and work_email)
        user = User.objects.filter(
            Q(email__iexact=email) | Q(employeeprofile__work_email__iexact=email)
        ).first()

        if not user:
            raise serializers.ValidationError({"email": "User not found."})

        # Fetch the most recent unused OTP for this exact user
        otp_obj = (
            PasswordResetOTP.objects
            .filter(user=user, is_used=False)
            .order_by("-created_at")
            .first()
        )

        # Strict sequential checks
        if not otp_obj:
            raise serializers.ValidationError(
                {"otp": "No active OTP found. Please request a new one."})

        if otp_obj.is_expired():
            raise serializers.ValidationError(
                {"otp": "OTP has expired. Please request a new one."})

        if not otp_obj.verify_otp(otp):
            raise serializers.ValidationError(
                {"otp": "Invalid OTP. Please try again."})

        # Pass the validated objects to the create method safely
        data["valid_otp_obj"] = otp_obj
        data["target_user"] = user

        return data

    def create(self, validated_data):
        email = validated_data["email"].lower()
        user = validated_data["target_user"]
        validated_otp_obj = validated_data["valid_otp_obj"]

        with transaction.atomic():
            # CRITICAL FIX: Lock the exact OTP row we already validated by its ID
            # This prevents replay attacks without breaking the work_email logic
            locked_otp = (
                PasswordResetOTP.objects
                .select_for_update()
                .get(id=validated_otp_obj.id)
            )

            if locked_otp.is_used:
                raise serializers.ValidationError(
                    "This OTP was just used in another request.")

            user.set_password(validated_data["new_password"])
            user.save(update_fields=["password"])

            locked_otp.is_used = True
            locked_otp.save(update_fields=["is_used"])

        return {"email": email}
