from django.contrib import admin
from .models import LoginSupportTicket


@admin.register(LoginSupportTicket)
class LoginSupportTicketAdmin(admin.ModelAdmin):
    list_display = ('email_or_empid', 'issue_type', 'resolved', 'created_at')
    list_filter = ('issue_type', 'resolved')
    search_fields = ('email_or_empid',)
