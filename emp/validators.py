# emp/validators.py

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
import os

MAX_FILE_MB = 5
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf"}


def validate_file_size(value: UploadedFile):
    # Enforce max upload size
    if value.size > MAX_FILE_MB * 1024 * 1024:
        raise ValidationError(
            f"File too large. Maximum size allowed is {MAX_FILE_MB} MB."
        )


def validate_image_extension(value: UploadedFile):
    # Prevent extension spoofing
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError("Unsupported file extension.")
