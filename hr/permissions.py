# hr/permissions.py
from rest_framework import permissions


class IsHR(permissions.BasePermission):
    """Allow only HR and management roles."""

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        role = (getattr(user, "role", "") or "").lower()
        return role in ("hr", "management")



class IsTL(permissions.BasePermission):
    """Allow only TL (team lead)."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, 'role', None) == 'tl')
