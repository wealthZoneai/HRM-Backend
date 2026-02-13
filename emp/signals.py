from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from emp.models import EmployeeProfile
from emp.utils import generate_emp_id

User = get_user_model()


@receiver(post_save, sender=User)
def create_employee_profile(sender, instance, created, **kwargs):
    """
    Automatically create EmployeeProfile for every new user.
    Works for superusers, admin users, shell users, and API users.
    """

    if not created:
        return

    # If profile already exists (safety check), skip
    if hasattr(instance, "employeeprofile"):
        return

    role = getattr(instance, "role", "employee")

    profile = EmployeeProfile.objects.create(
        user=instance,
        emp_id=generate_emp_id(),
        work_email=instance.email or f"{instance.username}@wealthzonegroupai.com",
        first_name=instance.first_name or "",
        last_name=instance.last_name or "",
        role=role,
        start_date=timezone.localdate(),
    )

    profile.save()
