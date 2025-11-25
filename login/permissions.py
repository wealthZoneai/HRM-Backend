from rest_framework.permissions import BasePermission


class IsManagement(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "management"


class IsHR(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "hr"


class IsTL(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "tl"


class IsEmployee(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "employee"


class IsIntern(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "intern"
