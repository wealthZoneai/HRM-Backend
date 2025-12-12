# emp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('my-profile/', views.MyProfileView.as_view(), name='my-profile'),

    path('my-profile/contact/', views.UpdateContactView.as_view(),
         name='my-profile-contact'),

    path('my-profile/identification/', views.UpdateIdentificationView.as_view(),
         name='my-profile-identification'),

    path('dashboard/summary/', views.DashboardSummaryAPIView.as_view(),
         name='dashboard-summary'),

    path('attendance/clock-in/', views.ClockInAPIView.as_view(), name='clock-in'),

    path('attendance/clock-out/', views.ClockOutAPIView.as_view(), name='clock-out'),

    path('attendance/days/', views.MyAttendanceDaysAPIView.as_view(),
         name='attendance-days'),

    path('calendar/', views.CalendarEventsAPIView.as_view(), name='calendar'),

    path("announcements/", views.emp_all_announcements,
         name="emp_all_announcements"),

    path('notifications/', views.emp_notifications, name="emp_notifications"),

    path('notifications/mark-read/', views.mark_notifications_read,
         name="mark_notifications_read"),

    path('tl-announcements/', views.emp_tl_announcements,
         name='employee_tl_announcements'),

    path('payroll/my-details/',
         views.MySalaryDetailsAPIView.as_view(), name='my-salary'),

    path('payroll/my-payslips/',
         views.MyPayslipsAPIView.as_view(), name='my-payslips'),

    path('payroll/my-payslips/<int:year>/<int:month>/download/',
         views.PayslipDownloadAPIView.as_view(), name='my-payslip-download'),

    path('leave/my-balance/', views.MyLeaveBalancesAPIView.as_view(),
         name='my-leave-balance'),

    path('leave/my-requests/', views.MyLeaveRequestsAPIView.as_view(),
         name='my-leave-requests'),

    path('leave/apply/', views.LeaveApplyAPIView.as_view(), name='leave-apply'),

    path('policy/', views.PolicyListAPIView.as_view(), name='policy-list'),

    path('policy/create/', views.PolicyCreateAPIView.as_view(), name='policy-create'),

    path('policy/<int:pk>/', views.PolicyUpdateDeleteAPIView.as_view(),
         name='policy-detail'),

    path('hr/create-employee/', views.HRCreateEmployeeAPIView.as_view(),
         name='hr-create-employee'),

    path('action/leave/<int:leave_id>/',
         views.HRTLActionAPIView.as_view(), name='tl-hr-leave-action'),

    path('timesheet/daily/update/', views.TimesheetDailyUpdateAPIView.as_view(),
         name='timesheet_daily_update'),

    path('timesheet/daily/form/', views.TimesheetDailyFormAPIView.as_view(),
         name='timesheet_daily_form'),

    path('timesheet/hr/daily/',
         views.TimesheetDailyForHRAPIView.as_view(),   name='timesheet_hr_daily'),

    path('timesheet/hr/monthly/',
         views.TimesheetMonthlyForHRAPIView.as_view(), name='timesheet_hr_monthly'),

    path('timesheet/hr/worksheet/',
         views.TimesheetWorksheetForHRAPIView.as_view(), name='timesheet_hr_worksheet'),

    path('timesheet/hr/yearly/',
         views.TimesheetYearlyForHRAPIView.as_view(),  name='timesheet_hr_yearly'),

    path('timesheet/tl/daily/',
         views.TimesheetDailyForTLAPIView.as_view(),    name='timesheet_tl_daily'),

    path('timesheet/tl/monthly/',
         views.TimesheetMonthlyForTLAPIView.as_view(),  name='timesheet_tl_monthly'),

    path('timesheet/tl/worksheet/',
         views.TimesheetWorksheetForTLAPIView.as_view(), name='timesheet_tl_worksheet'),

    path('timesheet/tl/yearly/',
         views.TimesheetYearlyForTLAPIView.as_view(),   name='timesheet_tl_yearly'),
]
