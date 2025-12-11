# emp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Profile
    path('my-profile/', views.MyProfileView.as_view(), name='my-profile'),
    path('my-profile/contact/', views.UpdateContactView.as_view(),
         name='my-profile-contact'),
    path('my-profile/identification/', views.UpdateIdentificationView.as_view(),
         name='my-profile-identification'),


    # Dashboard
    path('dashboard/summary/', views.DashboardSummaryAPIView.as_view(),
         name='dashboard-summary'),

    # Attendance
    path('attendance/clock-in/', views.ClockInAPIView.as_view(), name='clock-in'),
    path('attendance/clock-out/', views.ClockOutAPIView.as_view(), name='clock-out'),
    path('attendance/days/', views.MyAttendanceDaysAPIView.as_view(),
         name='attendance-days'),

    # Calendar
    path('calendar/', views.CalendarEventsAPIView.as_view(), name='calendar'),

    path("announcements/", views.emp_all_announcements, name="emp_all_announcements"),
    path('notifications/', views.emp_notifications, name="emp_notifications"),

    path('notifications/mark-read/', views.mark_notifications_read, name="mark_notifications_read"),
     path('tl-announcements/', views.emp_tl_announcements, name='employee_tl_announcements'),


    # Payroll
    path('payroll/my-details/',
         views.MySalaryDetailsAPIView.as_view(), name='my-salary'),
    path('payroll/my-payslips/',
         views.MyPayslipsAPIView.as_view(), name='my-payslips'),
    path('payroll/my-payslips/<int:year>/<int:month>/download/',
         views.PayslipDownloadAPIView.as_view(), name='my-payslip-download'),

    # Leave
    path('leave/my-balance/', views.MyLeaveBalancesAPIView.as_view(),
         name='my-leave-balance'),
    path('leave/my-requests/', views.MyLeaveRequestsAPIView.as_view(),
         name='my-leave-requests'),
    path('leave/apply/', views.LeaveApplyAPIView.as_view(), name='leave-apply'),

    # Policies
    path('policy/', views.PolicyListAPIView.as_view(), name='policy-list'),
    path('policy/create/', views.PolicyCreateAPIView.as_view(), name='policy-create'),
    path('policy/<int:pk>/', views.PolicyUpdateDeleteAPIView.as_view(), name='policy-detail'),

    # HR support
    path('hr/create-employee/', views.HRCreateEmployeeAPIView.as_view(),
         name='hr-create-employee'),
    path('action/leave/<int:leave_id>/',
         views.HRTLActionAPIView.as_view(), name='tl-hr-leave-action'),
]
