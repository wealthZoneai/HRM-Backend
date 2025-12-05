# HRM/emp/views_protected_media.py
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
import os
from .models import EmployeeProfile
from login.models import User

ALLOWED_FIELDS = {
    "aadhaar_image",
    "pan_image",
    "passport_image",
    "id_image",
    "profile_photo",
}


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def protected_employee_media(request, pk, field_name):
    """
    Serve media files for EmployeeProfile fields in a protected manner.
    Access rules:
      - Requesting user is the owner (employee.user == request.user)
      - OR requesting user has role that indicates HR/management (role-based)
    """

    profile = get_object_or_404(EmployeeProfile, pk=pk)

    if field_name not in ALLOWED_FIELDS:
        return Response({"detail": "Invalid media field."}, status=400)

    user = request.user

    is_hr = getattr(user, "role", None) in (
        "HR", "hr", "HR_MANAGER", "Management", "management")

    is_owner = False
    try:
        if profile.user == user:
            is_owner = True
    except Exception:
        is_owner = False

    if not (is_owner or is_hr):
        return Response({"detail": "You do not have permission to access this file."}, status=403)

    file_field = getattr(profile, field_name, None)
    if not file_field:
        return Response({"detail": "No file found."}, status=404)

    file_path = getattr(file_field, "path", None)
    if not file_path or not os.path.exists(file_path):
        raise Http404("File does not exist.")

    response = FileResponse(open(file_path, "rb"))
    return response
