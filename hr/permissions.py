from rest_framework.permissions import BasePermission
from login.models import User


class IsHR(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and
            user.role in (User.ROLE_HR, User.ROLE_MANAGEMENT)
        )


class IsTL(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and user.role == User.ROLE_TL
        )


class IsHRorDMorPM(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and
            user.role in (
                User.ROLE_HR,
                User.ROLE_MANAGEMENT,
                User.ROLE_DM,
                User.ROLE_PM,
            )
        )
