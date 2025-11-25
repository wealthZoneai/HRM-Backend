from django.contrib import admin
from .models import EmployeeProfile


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'emp_id', 'first_name',
                    'last_name', 'department', 'job_title')
    search_fields = ('user__username', 'emp_id',
                     'first_name', 'last_name', 'department')
