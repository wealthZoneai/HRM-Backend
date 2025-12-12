# login/views.py
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    CustomTokenSerializer,
    ForgotPasswordSerializer,
    VerifyOTPSerializer,
    ResetPasswordSerializer,
)
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer


class ForgotPasswordView(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = ForgotPasswordSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]


class VerifyOTPView(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = VerifyOTPSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]


class ResetPasswordView(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
