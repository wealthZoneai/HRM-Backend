from rest_framework.permissions import BasePermission


class Ismanagement(BasePermission):

    def has_permission(self, request, view):

        if request.user and request.user.is_authenticated:
            return request.user.role.lower() == "ceo"

        return False