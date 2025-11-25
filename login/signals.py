from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from emp.models import EmployeeProfile

User = get_user_model()


def generate_username(first_name, last_name):
    base = f"{first_name.lower()}.{last_name.lower()}"
    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}{counter}"
        counter += 1
    return username


def generate_work_email(first_name, last_name):
    domain = "wealthzonegroupai.com"
    base = f"{first_name.lower()}.{last_name.lower()}"
    email = f"{base}@{domain}"
    counter = 1
    while User.objects.filter(email=email).exists():
        email = f"{base}{counter}@{domain}"
        counter += 1
    return email


def generate_emp_id():
    from emp.models import EmployeeProfile
    last_profile = EmployeeProfile.objects.order_by('-id').first()
    if not last_profile:
        next_number = 1
    else:
        # extract number from last emp_id (WZG-AI-xxxx)
        try:
            last_num = int(last_profile.emp_id.split("-")[-1])
            next_number = last_num + 1
        except:
            next_number = last_profile.id + 1

    return f"WZG-AI-{next_number:04d}"


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if not created:
        return

    # Skip HR and Management - they are not employees
    if getattr(instance, "role", None) in ["hr", "management"]:
        return

    # Auto-generate username if missing
    if not instance.username:
        instance.username = generate_username(
            instance.first_name, instance.last_name)
        instance.save()

    # Auto-generate work email if missing
    if not instance.email:
        instance.email = generate_work_email(
            instance.first_name, instance.last_name)
        instance.save()

    # Create profile if not exists
    EmployeeProfile.objects.get_or_create(
        user=instance,
        defaults={
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "emp_id": generate_emp_id(),
            "work_email": instance.email,
            "role": getattr(instance, "role", "employee"),
        }
    )
