from rest_framework.permissions import BasePermission


class IsDM(BasePermission):
    def has_permission(self, request, view):
        has_perm = request.user.is_authenticated and request.user.role in ('management', 'dm')
        print(f"DEBUG: IsDM check for {request.user} (Role: {request.user.role}) -> {has_perm}")
        return has_perm


class IsPM(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'pm'


class IsTL(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'tl'


class IsEmployee(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ('employee', 'intern')
