from django.contrib import admin
from .models import User, PasswordResetOTP

admin.site.register(User)


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    readonly_fields = ("otp_hash", "created_at")
