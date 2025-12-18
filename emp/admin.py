# emp/admin.py
from django.contrib import admin
from . import models
from .models import SalaryStructure, EmployeeSalary, Payslip


@admin.register(models.EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('emp_id', 'full_name', 'work_email', 'role', 'is_active')
    search_fields = ('emp_id', 'first_name', 'last_name', 'work_email')


@admin.register(models.Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'to_user', 'notif_type', 'is_read', 'created_at')
    list_filter = ('notif_type', 'is_read')


@admin.register(models.Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'clock_in',
                    'clock_out', 'duration_time', 'status')
    list_filter = ('status', 'date')


@admin.register(models.Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_time', 'end_time')


@admin.register(models.LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')


@admin.register(models.LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('profile', 'leave_type', 'total_allocated', 'used')


@admin.register(models.LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('profile', 'leave_type', 'start_date',
                    'end_date', 'days', 'status')


@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'monthly_ctc',
        'basic_percent',
        'hra_percent',
        'overtime_multiplier'
    )
    search_fields = ('name',)


@admin.register(EmployeeSalary)
class EmployeeSalaryAdmin(admin.ModelAdmin):
    list_display = (
        'profile',
        'structure',
        'effective_from',
        'is_active'
    )
    list_filter = ('is_active',)


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = (
        'profile',
        'year',
        'month',
        'gross_amount',
        'net_amount',
        'finalized'
    )
    list_filter = ('year', 'month', 'finalized')


@admin.register(models.Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ('title', 'policy_type', 'created_at')
