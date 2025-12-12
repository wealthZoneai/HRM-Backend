# login/permissions.py 

from rest_framework.permissions import BasePermission


class RolePermission(BasePermission):
    """
    Generic role permission: subclass and set `required_role` attribute.
    """

    required_role = None

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        role = getattr(user, "role", "") or ""
        return role.lower() == (self.required_role or "").lower()


class IsManagement(RolePermission):
    required_role = "management"


class IsHR(RolePermission):
    required_role = "hr"


class IsTL(RolePermission):
    required_role = "tl"


class IsEmployee(RolePermission):
    required_role = "employee"


class IsIntern(RolePermission):
    required_role = "intern"
