from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenSerializer
from rest_framework import status
from rest_framework import generics
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .serializers import (
    ForgotPasswordSerializer,
    VerifyOTPSerializer,
    ResetPasswordSerializer,
)


class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer


class ForgotPasswordView(CreateAPIView):
    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # serializer.create() will perform the OTP generation + send
        serializer.save()
        return Response({"message": "OTP sent to your email."}, status=status.HTTP_200_OK)


class VerifyOTPView(CreateAPIView):
    serializer_class = VerifyOTPSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()  # marks otp used
        return Response({"message": "OTP verified successfully."}, status=status.HTTP_200_OK)


class ResetPasswordView(CreateAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()  # sets the new password
        return Response({"message": "Password reset successful. You can now log in."}, status=status.HTTP_200_OK)
