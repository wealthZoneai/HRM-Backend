from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PasswordResetOTP
from .utils import generate_otp, send_otp_email


class CustomTokenSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['role'] = user.role

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Add extra response data for frontend redirection
        data['role'] = self.user.role
        data['username'] = self.user.username

        # Dashboard redirect slug
        role_redirects = {
            "management": "/dashboard/management",
            "hr": "/dashboard/hr",
            "tl": "/dashboard/tl",
            "employee": "/dashboard/employee",
            "intern": "/dashboard/intern",
        }

        data['redirect_url'] = role_redirects.get(self.user.role, "/")

        return data


User = get_user_model()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        email = value.lower()

        # PRODUCTION CHECK:
        # if not email.endswith("@wealthzonegroupai.com"):
        #     raise serializers.ValidationError("Only company email accounts can request password reset.")

        return email

    def create(self, validated_data):
        email = validated_data['email']
        user = User.objects.filter(email=email).first()

        if not user:
            raise serializers.ValidationError(
                {"email": "Email not found in HRMS system."})

        # generate OTP
        otp_code = generate_otp()

        PasswordResetOTP.objects.create(user=user, otp=otp_code)

        # send email
        send_otp_email(email, otp_code)

        return {"message": "OTP sent to your email."}


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4)

    def validate(self, data):
        email = data['email']
        otp = data['otp']

        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError({"email": "Email not found."})

        otp_obj = PasswordResetOTP.objects.filter(
            user=user, otp=otp, is_used=False).last()
        if not otp_obj:
            raise serializers.ValidationError({"otp": "Invalid OTP."})

        if otp_obj.is_expired():
            raise serializers.ValidationError({"otp": "OTP expired."})

        data['user'] = user
        data['otp_obj'] = otp_obj
        return data

    def create(self, validated_data):
        otp_obj = validated_data['otp_obj']
        otp_obj.is_used = True  # Mark OTP as used
        otp_obj.save()
        return {"message": "OTP verified successfully."}


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."})

        pwd = data['new_password']

        # Password validation rules:
        if len(pwd) < 8:
            raise serializers.ValidationError(
                {"new_password": "Password must be at least 8 characters long."})
        if not any(c.isdigit() for c in pwd):
            raise serializers.ValidationError(
                {"new_password": "Password must contain a number."})
        if not any(c.isupper() for c in pwd):
            raise serializers.ValidationError(
                {"new_password": "Password must contain an uppercase character."})
        if not any(c.islower() for c in pwd):
            raise serializers.ValidationError(
                {"new_password": "Password must contain a lowercase character."})
        if not any(c in "!@#$%^&*()_+{}[]|:;'<>,.?/" for c in pwd):
            raise serializers.ValidationError(
                {"new_password": "Password must contain a special character."})

        return data

    def create(self, validated_data):
        user = User.objects.filter(email=validated_data['email']).first()
        if not user:
            raise serializers.ValidationError({"email": "Email not found."})

        # Update password
        user.set_password(validated_data['new_password'])
        user.save()

        return {"message": "Password reset successful. You can now log in."}
