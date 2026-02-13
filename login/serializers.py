from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import PasswordResetOTP
from .utils import generate_otp, send_otp_email
import re

User = get_user_model()


class CustomTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["username"] = user.username
        return token


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def create(self, validated_data):
        email = validated_data["email"].lower()
        user = User.objects.filter(email=email).first()

        if not user:
            return {"email": email}  # avoid email enumeration

        otp = generate_otp()
        PasswordResetOTP.create_otp(user, otp)
        send_otp_email(email, otp)

        return {"email": email}


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        validate_password(data["new_password"])

        if not re.search(r"[A-Z]", data["new_password"]):
            raise serializers.ValidationError(
                "Password must contain uppercase letter")

        if not re.search(r"[0-9]", data["new_password"]):
            raise serializers.ValidationError("Password must contain a number")

        return data

    def create(self, validated_data):
        email = validated_data["email"].lower()
        otp = validated_data["otp"]

        with transaction.atomic():
            # Lock OTP rows to prevent replay attacks
            otp_obj = (
                PasswordResetOTP.objects
                .select_for_update()
                .filter(user__email=email, is_used=False)
                .order_by("-created_at")
                .first()
            )

            if not otp_obj or otp_obj.is_expired() or not otp_obj.verify_otp(otp):
                raise serializers.ValidationError("Invalid or expired OTP")

            user = otp_obj.user
            user.set_password(validated_data["new_password"])
            user.save(update_fields=["password"])

            otp_obj.is_used = True
            otp_obj.save(update_fields=["is_used"])

        return {"email": email}
