from rest_framework.permissions import BasePermission

class IsTicketOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user

class IsSupportStaff(BasePermission):
    def has_permission(self, request, view):
        role = getattr(request.user, 'role', '')
        return role in ('hr', 'management', 'it')

