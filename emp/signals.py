# emp/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.conf import settings
from .models import EmployeeProfile
from django.utils.crypto import get_random_string
from django.utils import timezone

User = get_user_model()


def generate_username(first_name, last_name):
    base = f"{(first_name or '').strip().lower()}.{(last_name or '').strip().lower()}"
    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}{counter}"
        counter += 1
    return username


def generate_work_email(first_name, last_name):
    domain = getattr(settings, 'DEFAULT_COMPANY_DOMAIN',
                     'wealthzonegroupai.com')
    base = f"{(first_name or '').strip().lower()}.{(last_name or '').strip().lower()}"
    email = f"{base}@{domain}"
    counter = 1
    while User.objects.filter(email=email).exists():
        email = f"{base}{counter}@{domain}"
        counter += 1
    return email


@receiver(post_save, sender=User)
def create_employee_profile(sender, instance, created, **kwargs):
    if not created:
        return

    if not instance.username:
        instance.username = generate_username(
            instance.first_name or 'user',
            instance.last_name or get_random_string(4)
        )
        instance.save(update_fields=['username'])

    if not instance.email:
        instance.email = generate_work_email(
            instance.first_name or 'user',
            instance.last_name or get_random_string(4)
        )
        instance.save(update_fields=['email'])
