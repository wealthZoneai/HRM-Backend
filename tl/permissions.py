# tl/permissions.py
from rest_framework import permissions


class IsTL(permissions.BasePermission):
    """Allow only Team Leaders."""

    def has_permission(self, request, view):
        role = getattr(request.user, "role", "") or ""
        return bool(request.user and request.user.is_authenticated and role.lower() == "tl")
