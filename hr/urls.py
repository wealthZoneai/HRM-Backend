# hr/urls.py
from django.urls import path
from . import views

app_name = 'hr'

urlpatterns = [

    path('employees/', views.HRListEmployeesAPIView.as_view(),
         name='hr-employees-list'),

    path('employees/<int:pk>/', views.HRRetrieveEmployeeAPIView.as_view(),
         name='hr-employee-detail'),

    path('employees/<int:pk>/job&bank/',
         views.HRUpdateJobBankAPIView.as_view(), name='hr-employee-jobbank'),

    path('attendance/', views.HRAttendanceListAPIView.as_view(),
         name='hr-attendance-list'),

    path('attendance/<int:pk>/', views.HRAttendanceRetrieveAPIView.as_view(),
         name='hr-attendance-detail'),

    path('attendance/<int:attendance_id>/correct/',
         views.HRAttendanceCorrectAPIView.as_view(), name='hr-attendance-correct'),

    path('calendar/create/', views.HRCalendarCreateAPIView.as_view(),
         name='hr-calendar-create'),

    path('calendar/<int:pk>/update/',
         views.HRCalendarUpdateAPIView.as_view(), name='calendar_update'),

    path('calendar/<int:pk>/delete/',
         views.HRCalendarDeleteAPIView.as_view(), name='calendar_update'),

    path("announcement/create/", views.create_announcement,
         name="api_create_announcement"),

    path('announcement/list/', views.list_announcements, name='anouncements_list'),

    path('announcement/<int:pk>/update/',
         views.update_announcement, name='update-announcement'),

    path('announcement/<int:pk>/delete/',
         views.delete_announcement, name='delete-announcement'),

    path("tl-announcements/", views.emp_tl_announcements,
         name="emp_tl_announcements"),

    path('salary-structures/', views.SalaryStructureListCreateAPIView.as_view(),
         name='hr-salary-structures'),

    path('employees/<int:profile_id>/assign-salary/',
         views.EmployeeSalaryAssignAPIView.as_view(), name='hr-assign-salary'),

    path('employees/<int:profile_id>/generate-payslip/',
         views.HRGeneratePayslipAPIView.as_view(), name='hr-generate-payslip'),

    path('leaves/', views.HRLeaveListAPIView.as_view(), name='hr-leave-list'),

    path('leaves/<int:pk>/', views.HRLeaveDetailAPIView.as_view(),
         name='hr-leave-detail'),

    path('leaves/<int:leave_id>/action/',
         views.HRLeaveActionAPIView.as_view(), name='hr-leave-action'),
]
