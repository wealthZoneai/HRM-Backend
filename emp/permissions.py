# emp/permissions.py

from rest_framework.permissions import BasePermission
from login.models import User


class IsHROrManagement(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and
            user.role in (User.ROLE_HR, User.ROLE_MANAGEMENT)
        )


class IsTLOnly(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and user.role == User.ROLE_TL
        )


class IsTLorHRorOwner(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.role in (User.ROLE_HR, User.ROLE_MANAGEMENT):
            return True

        profile = getattr(obj, "profile", None)
        if profile and profile.user == user:
            return True

        if user.role == User.ROLE_TL and getattr(obj, "tl", None) == user:
            return True

        return False
