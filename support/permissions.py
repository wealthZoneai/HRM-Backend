from rest_framework.permissions import BasePermission
from login.models import User


class IsTicketOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user


class IsSupportStaff(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and
            user.role in (
                User.ROLE_HR,
                User.ROLE_MANAGEMENT,
                User.ROLE_IT,
            )
        )
