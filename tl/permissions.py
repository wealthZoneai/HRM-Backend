from rest_framework.permissions import BasePermission
from login.models import User


class IsTL(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and
            user.role == User.ROLE_TL
        )
