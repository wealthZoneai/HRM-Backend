# emp/permissions.py
from rest_framework.permissions import BasePermission
import logging

logger = logging.getLogger(__name__)


class IsHROrManagement(BasePermission):
    """
    Allows access only to HR or Management roles.
    Assumes user.role is a lower-case string like 'hr' or 'management'.
    """

    def has_permission(self, request, view):
        user = request.user
        allowed = bool(user and user.is_authenticated and getattr(
            user, "role", None) in ("hr", "management"))
        if not allowed:
            logger.info("Permission denied: user=%s role=%s path=%s", getattr(
                user, "id", None), getattr(user, "role", None), request.path)
        return allowed


class IsTLorHRorOwner(BasePermission):
    """
    HR -> can access all
    TL -> can access employees they lead (employeeprofile.team_lead == user)
    Owner -> can access own data
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def _get_profile_from_obj(self, obj):

        try:
            profile = getattr(obj, "profile", None) or obj
        except Exception:
            profile = None
        return profile

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if getattr(user, "role", None) in ("hr", "management"):
            return True

        profile = self._get_profile_from_obj(obj)

        try:
            if profile and getattr(profile, "user", None) == user:
                return True
        except Exception:
            pass

        if getattr(user, "role", None) == "tl":
            try:
                employee_user = getattr(profile, "user", None)
                if not employee_user:
                    return False
                team_lead = getattr(
                    employee_user.employeeprofile, "team_lead", None)
                return team_lead == user
            except Exception:
                return False

        return False


class IsTLOnly(BasePermission):
    """
    Only Team Leads (role == 'tl' or flag user.is_tl or group TL)
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "role", None) == "tl":
            return True
        if getattr(user, "is_tl", False):
            return True
        try:
            if user.groups.filter(name__in=["TL", "TeamLead"]).exists():
                return True
        except Exception:
            pass
        return False
