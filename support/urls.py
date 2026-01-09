from django.urls import path
from .views import *

app_name = 'support'

urlpatterns = [
    path('tickets/create/', CreateSupportTicketAPIView.as_view()),
    path('tickets/my/', MySupportTicketsAPIView.as_view()),
    path('tickets/<int:ticket_id>/', SupportTicketDetailAPIView.as_view()),
    path('tickets/<int:ticket_id>/message/',
         SendSupportMessageAPIView.as_view()),
    path('support/queue/', SupportQueueAPIView.as_view()),
    path('login-issues/create/', CreateLoginSupportTicketAPIView.as_view()),

]
