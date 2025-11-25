from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('verify-otp/', views.VerifyOTPView.as_view(), name='verify-otp'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),
]
