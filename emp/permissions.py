from rest_framework.permissions import BasePermission

class IsHRorManagement(BasePermission):
    """
    Allow access if user.role is 'hr' or 'management'.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return getattr(user, 'role', None) in ('hr', 'management')

class IsOwnerOrHRorManagement(BasePermission):
    """
    Object-level permission: allow if owner (user of the profile) or HR/Management
    """
    def has_object_permission(self, request, view, obj):
        # obj is EmployeeProfile instance
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, 'role', None) in ('hr', 'management'):
            return True
        return obj.user == user
