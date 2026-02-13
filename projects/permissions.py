from rest_framework.permissions import BasePermission
from login.models import User


class IsDM(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and
            user.role in (User.ROLE_MANAGEMENT, User.ROLE_DM)
        )


class IsPM(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and user.role == User.ROLE_PM
        )


class IsTL(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and user.role == User.ROLE_TL
        )


class IsEmployee(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and
            user.role in (User.ROLE_EMPLOYEE, User.ROLE_INTERN)
        )
