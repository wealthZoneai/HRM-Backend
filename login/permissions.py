from rest_framework.permissions import BasePermission
from .models import User


class RolePermission(BasePermission):
    allowed_roles = []

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.role in self.allowed_roles


class IsManagement(RolePermission):
    allowed_roles = [User.ROLE_MANAGEMENT]


class IsDM(RolePermission):
    allowed_roles = [User.ROLE_DM]


class IsPM(RolePermission):
    allowed_roles = [User.ROLE_PM]


class IsHR(RolePermission):
    allowed_roles = [User.ROLE_HR]


class IsTL(RolePermission):
    allowed_roles = [User.ROLE_TL]


class IsEmployee(RolePermission):
    allowed_roles = [User.ROLE_EMPLOYEE]


class IsIntern(RolePermission):
    allowed_roles = [User.ROLE_INTERN]
