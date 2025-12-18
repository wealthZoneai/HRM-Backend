# login/serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PasswordResetOTP
from .utils import generate_otp, send_otp_email
from django.db import transaction
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
import re


User = get_user_model()


class CustomTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["username"] = user.username
        token["email"] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["role"] = self.user.role
        data["username"] = self.user.username

        role_redirects = {
            "management": "/dashboard/management",
            "hr": "/dashboard/hr",
            "tl": "/dashboard/tl",
            "employee": "/dashboard/employee",
            "intern": "/dashboard/intern",
        }

        data["redirect_url"] = role_redirects.get(self.user.role, "/")
        return data


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        email = value.lower()
        return email

    def create(self, validated_data):
        email = validated_data["email"]
        user = User.objects.filter(email=email).first()

        if not user:
            return {"email": email}

        existing = PasswordResetOTP.objects.filter(
            user=user, is_used=False).order_by('-id').first()
        if existing and not existing.is_expired():
            return {"email": email}

        otp = generate_otp()
        PasswordResetOTP.objects.create(user=user, otp=otp)

        try:
            send_otp_email(email, otp)
        except Exception:
            pass

        return {"email": email}


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)

    def validate(self, data):
        email = data["email"].lower()
        otp = data["otp"]

        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError({"email": "Email not found."})

        otp_obj = PasswordResetOTP.objects.filter(
            user=user, otp=otp, is_used=False
        ).order_by('-id').first()

        if not otp_obj:
            raise serializers.ValidationError({"otp": "Invalid OTP."})

        if otp_obj.is_expired():
            raise serializers.ValidationError({"otp": "OTP expired."})

        # keep otp_obj for potential downstream use
        data["user"] = user
        data["otp_obj"] = otp_obj
        return data

    def create(self, validated_data):
        # Mark OTP as used to prevent replay
        otp_obj = validated_data.get("otp_obj")
        if otp_obj:
            otp_obj.is_used = True
            otp_obj.save(update_fields=["is_used"])
        return {
            "email": validated_data["email"],
            "otp": validated_data["otp"]
        }


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6, write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        # 1. Match passwords
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match"}
            )

        pwd = data["new_password"]

        # 2. Run Django validators (length, common, numeric, similarity)
        try:
            validate_password(pwd, user=None)
        except DjangoValidationError as e:
            raise serializers.ValidationError(
                {"new_password": list(e.messages)})

        # 3. Enforce uppercase
        if not re.search(r"[A-Z]", pwd):
            raise serializers.ValidationError({
                "new_password": "Password must contain at least one uppercase letter."
            })

        # 4. Enforce lowercase
        if not re.search(r"[a-z]", pwd):
            raise serializers.ValidationError({
                "new_password": "Password must contain at least one lowercase letter."
            })

        # 5. Enforce special character
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", pwd):
            raise serializers.ValidationError({
                "new_password": "Password must contain at least one special character."
            })

        # 6. OTP verification (unchanged)
        email = data["email"].lower()
        otp = data["otp"]

        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError({"email": "Email not found."})

        otp_obj = PasswordResetOTP.objects.filter(
            user=user, otp=otp, is_used=False
        ).order_by("-id").first()

        if not otp_obj:
            raise serializers.ValidationError({"otp": "Invalid or used OTP."})

        if otp_obj.is_expired():
            raise serializers.ValidationError({"otp": "OTP expired."})

        data["user_obj"] = user
        data["otp_obj"] = otp_obj
        return data

    def create(self, validated_data):
        user = validated_data["user_obj"]
        otp_obj = validated_data["otp_obj"]

        with transaction.atomic():
            user.set_password(validated_data["new_password"])
            user.save(update_fields=["password"])
            otp_obj.is_used = True
            otp_obj.save(update_fields=["is_used"])

        return {"email": user.email}
