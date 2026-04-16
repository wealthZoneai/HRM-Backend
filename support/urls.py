from django.urls import path
from .views import (
    CreateSupportTicketAPIView,
    MySupportTicketsAPIView,
    SupportTicketDetailAPIView,
    SendSupportMessageAPIView,
    SupportQueueAPIView,
    CreateLoginSupportTicketAPIView
)

app_name = 'support'

urlpatterns = [

    path('tickets/', MySupportTicketsAPIView.as_view(), name='ticket-list'),
    path('tickets/create/', CreateSupportTicketAPIView.as_view(), name='ticket-create'),
    path('tickets/<int:ticket_id>/', SupportTicketDetailAPIView.as_view(), name='ticket-detail'),
    path('tickets/<int:ticket_id>/messages/', SendSupportMessageAPIView.as_view(), name='ticket-message'),
 
    # Support Queue (Admin/HR/IT)
    path('tickets/queue/', SupportQueueAPIView.as_view(), name='ticket-queue'),
 
    # Login Issues
    path('login-issues/', CreateLoginSupportTicketAPIView.as_view(), name='login-issue-create'),
    
]