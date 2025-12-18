from django.contrib import admin
from .models import Announcement, TLAnnouncement, SalaryStructure, Payslip

admin.site.register(Announcement)
admin.site.register(TLAnnouncement)


@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "monthly_ctc",
        "basic_percent",
        "hra_percent",
        "overtime_multiplier",
    )
    search_fields = ("name",)


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = (
        "profile",
        "year",
        "month",
        "gross_amount",
        "net_amount",
        "finalized",
    )
    list_filter = ("year", "month", "finalized")
