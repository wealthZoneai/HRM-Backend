# emp/permissions.py
from rest_framework import permissions
import logging
logger = logging.getLogger(__name__)


class IsHROrManagement(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        ok = bool(user and user.is_authenticated and getattr(
            user, 'role', None) in ('hr', 'management'))
        if not ok:
            logger.info("Permission denied for user=%s role=%s path=%s", getattr(
                user, 'id', None), getattr(user, 'role', None), request.path)
        return ok


class IsTLorHRorOwner(permissions.BasePermission):
    """
    TL or HR or the owner (employee) can access/modify.
    For leave objects, TL is team lead of the profile (profile.team_lead == user)
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, 'role', None) in ('hr', 'management'):
            return True
        if getattr(user, 'role', None) == 'tl':
            try:
                profile = getattr(obj, 'profile', None) or obj
                owner_user = getattr(profile, 'user', None)
                if not owner_user:
                    return False
                tl_user = getattr(owner_user.employeeprofile,
                                  'team_lead', None)
                # compare by id
                return getattr(tl_user, 'id', None) == getattr(user, 'id', None)
            except Exception:
                return False
        # owner fallback
        try:
            profile = getattr(obj, 'profile', None)
            if profile:
                return profile.user == user
            owner_user = getattr(obj, 'user', None)
            return owner_user == user
        except Exception:
            return False




from rest_framework.permissions import BasePermission
import logging

logger = logging.getLogger(__name__)


# -------------------------------------------------------
# HR & Management
# -------------------------------------------------------
class IsHROrManagement(BasePermission):
    """
    Allows access only to HR or Management roles.
    Assumes: user.role in ('hr', 'management')
    """

    def has_permission(self, request, view):
        user = request.user
        allowed = bool(
            user and user.is_authenticated and getattr(user, "role", None) in ("hr", "management")
        )
        if not allowed:
            logger.info(
                "Permission denied: user=%s role=%s path=%s",
                getattr(user, "id", None),
                getattr(user, "role", None),
                request.path,
            )
        return allowed


# -------------------------------------------------------
# TL → can access employees who report to them
# HR → can access all
# OWNER → can access their own timesheet
# -------------------------------------------------------
class IsTLorHRorOwner(BasePermission):
    """
    Access Rules:
        ✔ HR → can access all employees
        ✔ TL → can access employees where employeeprofile.team_lead == request.user
        ✔ Owner → can access their own data
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # HR / management → full access
        if getattr(user, "role", None) in ("hr", "management"):
            return True

        # Extract profile from obj (TimesheetEntry, TimesheetDay, EmployeeProfile)
        try:
            profile = getattr(obj, "profile", None) or obj
        except Exception:
            profile = None

        # Owner logic
        try:
            if profile and profile.user == user:
                return True
        except Exception:
            pass

        # TL logic
        if getattr(user, "role", None) == "tl":
            try:
                employee_user = profile.user
                team_lead = getattr(employee_user.employeeprofile, "team_lead", None)
                return team_lead == user
            except Exception:
                return False

        return False


# -------------------------------------------------------
# TL ONLY (for TL endpoints)
# -------------------------------------------------------
class IsTLOnly(BasePermission):
    """
    Allows access only to Team Leads.
    Must match your project's TL rule:
        - user.role == 'tl'
        - OR user.is_tl = True
        - OR group membership 'TL'
    """

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        # 1) Role-based
        if getattr(user, "role", None) == "tl":
            return True

        # 2) Boolean flag
        if getattr(user, "is_tl", False):
            return True

        # 3) Group-based
        try:
            if user.groups.filter(name__in=["TL", "TeamLead"]).exists():
                return True
        except Exception:
            pass

        return False
