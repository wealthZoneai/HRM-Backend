import os
import csv
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save

from emp.models import EmployeeProfile
from emp.signals import create_employee_profile

User = get_user_model()


class Command(BaseCommand):
    help = "Import employees from CSV"

    def handle(self, *args, **kwargs):

        file_path = os.path.join(settings.BASE_DIR, "employees.csv")

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR("employees.csv file not found"))
            return

        # Disable signal temporarily
        post_save.disconnect(create_employee_profile, sender=User)

        try:
            with open(file_path, newline="", encoding="latin-1") as file:

                reader = csv.DictReader(file)

                for row in reader:

                    emp_id = (row.get("emp_id") or "").strip()
                    email = (row.get("work_email") or "").strip()

                    if not emp_id or not email:
                        self.stdout.write(
                            self.style.WARNING(f"Skipping row: {row}"))
                        continue

                    # Skip duplicate employee
                    if EmployeeProfile.objects.filter(emp_id=emp_id).exists():
                        self.stdout.write(self.style.WARNING(
                            f"Already exists: {emp_id}"))
                        continue

                    username = email.split("@")[0]

                    # Create user
                    user, created = User.objects.get_or_create(
                        email=email,
                        defaults={
                            "username": username,
                            "first_name": row.get("first_name", ""),
                            "last_name": row.get("last_name", ""),
                        }
                    )

                    # Create employee profile
                    EmployeeProfile.objects.create(
                        user=user,
                        emp_id=emp_id,
                        work_email=email,
                        username=username,

                        first_name=row.get("first_name", ""),
                        last_name=row.get("last_name", ""),
                        middle_name=row.get("middle_name", ""),

                        personal_email=row.get("personal_email", ""),
                        phone_number=row.get("phone_number", ""),
                        alternate_number=row.get("alternate_number", ""),

                        dob=row.get("dob") or None,
                        blood_group=row.get("blood_group", ""),
                        gender=row.get("gender", ""),
                        marital_status=row.get("marital_status", ""),

                        profile_photo=row.get("profile_photo", ""),

                        aadhaar_number=row.get("aadhaar_number", ""),
                        aadhaar_front_image=row.get("aadhaar_front_image", ""),
                        aadhaar_back_image=row.get("aadhaar_back_image", ""),

                        pan=row.get("pan", ""),
                        pan_front_image=row.get("pan_front_image", ""),
                        pan_back_image=row.get("pan_back_image", ""),

                        passport_number=row.get("passport_number", ""),
                        id_card_number=row.get("id_card_number", ""),

                        job_title=row.get("job_title", ""),
                        department=row.get("department", ""),
                        designation=row.get("designation", ""),

                        date_of_joining=row.get("date_of_joining") or None,
                        employment_type=row.get("employment_type", ""),
                        start_date=row.get("start_date") or None,

                        location=row.get("location", ""),
                        job_description=row.get("job_description", ""),
                        id_image=row.get("id_image", ""),

                        bank_name=row.get("bank_name", ""),
                        account_number=row.get("account_number", ""),
                        ifsc_code=row.get("ifsc_code", ""),
                        branch=row.get("branch", ""),

                        role=row.get("role", "employee"),
                        is_active=row.get("is_active", "True").lower() in [
                            "true", "1", "yes"],

                        team_lead_id=row.get("team_lead_id") or None
                    )

                    self.stdout.write(
                        self.style.SUCCESS(f"Imported: {emp_id}"))

        finally:
            # Enable signal again
            post_save.connect(create_employee_profile, sender=User)

        self.stdout.write(self.style.SUCCESS("CSV Import Completed"))
