import csv
from datetime import datetime

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import transaction

from emp.models import EmployeeProfile

User = get_user_model()


class Command(BaseCommand):
    help = "Import existing employees with manual emp_id and work_email"

    @transaction.atomic
    def handle(self, *args, **kwargs):

        # ---------- OPEN CSV (handles Excel BOM safely) ----------
        with open("employees_import.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            if not reader.fieldnames:
                raise ValueError("CSV file has no header row")

            # ---------- NORMALIZE HEADERS (BOM + spaces + case) ----------
            reader.fieldnames = [
                h.replace("\ufeff", "").strip().lower()
                for h in reader.fieldnames
            ]

            self.stdout.write(
                self.style.WARNING(
                    f"Normalized CSV headers: {reader.fieldnames}"
                )
            )

            # ---------- REQUIRED COLUMNS (BASED ON YOUR emp MODELS) ----------
            required_columns = {
                "emp_id",
                "first_name",
                "last_name",
                "work_email",
                "username",
                "department",
                "designation",
                "date_of_joining",
                "role",
            }

            missing = required_columns - set(reader.fieldnames)
            if missing:
                raise ValueError(f"CSV missing columns: {missing}")

            # ---------- PROCESS EACH ROW ----------
            for raw_row in reader:

                # Skip fully empty rows (Excel junk)
                if not any(raw_row.values()):
                    continue

                # Normalize row keys
                row = {
                    k.replace("\ufeff", "").strip().lower(): (v or "")
                    for k, v in raw_row.items()
                }

                emp_id = row["emp_id"].strip()
                email = row["work_email"].strip().lower()

                if not emp_id:
                    self.stdout.write(
                        self.style.ERROR("Skipped row: emp_id is empty")
                    )
                    continue

                if not email:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Skipped emp_id={emp_id}: work_email is empty"
                        )
                    )
                    continue

                # Skip if user already exists
                if User.objects.filter(email=email).exists():
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipped existing user: {email}"
                        )
                    )
                    continue

                # ---------- DATE PARSING (DD-MM-YYYY → DATE) ----------
                raw_doj = row["date_of_joining"].strip()
                try:
                    date_of_joining = datetime.strptime(
                        raw_doj, "%d-%m-%Y"
                    ).date()
                except ValueError:
                    raise ValueError(
                        f"Invalid date_of_joining '{raw_doj}' "
                        f"for emp_id={emp_id}. Expected DD-MM-YYYY"
                    )

                # ---------- PASSWORD (OPTIONAL) ----------
                raw_password = row.get("password", "").strip()
                if raw_password:
                    password = make_password(raw_password)
                else:
                    # No password → user must reset
                    password = make_password(None)

                # ---------- CREATE USER ----------
                user = User.objects.create(
                    username=row["username"].strip(),
                    email=email,
                    first_name=row["first_name"].strip(),
                    last_name=row["last_name"].strip(),
                    role=row["role"].strip(),
                    password=password,
                    is_active=True,
                )

                # ---------- CREATE EMPLOYEE PROFILE ----------
                EmployeeProfile.objects.create(
                    user=user,
                    emp_id=emp_id,
                    work_email=email,
                    first_name=row["first_name"].strip(),
                    last_name=row["last_name"].strip(),
                    phone_number=row.get("phone_number", "").strip(),
                    department=row["department"].strip(),
                    designation=row["designation"].strip(),
                    date_of_joining=date_of_joining,
                    role=row["role"].strip(),
                    is_active=True,
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Imported: {emp_id} | {email}"
                    )
                )
