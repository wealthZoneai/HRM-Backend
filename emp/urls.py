from django.urls import path
from . import views

urlpatterns = [
    path('create-employee/', views.EmployeeCreateAPIView.as_view(),
         name='create-employee'),
    path('employee-list/', views.EmployeeListAPIView.as_view(), name='employee-list'),
    path('employees/<int:pk>/',
         views.EmployeeRetrieveUpdateAPIView.as_view(), name='employee-detail'),
    path('my-profile/', views.MyProfileAPIView.as_view(), name='my-profile'),

    path('attendance/clock-in/', views.ClockInAPIView.as_view(),
         name='attendance-clock-in'),
    path('attendance/clock-out/', views.ClockOutAPIView.as_view(),
         name='attendance-clock-out'),
    path('attendance/my-monthly/', views.MyAttendanceMonthlyAPIView.as_view(),
         name='attendance-my-monthly'),
    path('attendance/my-today/', views.MyAttendanceTodayStatusAPIView.as_view(),
         name='attendance-my-today'),
    path('attendance/hr/employee/<int:user_id>/',
         views.HREmployeeAttendanceAPIView.as_view(), name='attendance-hr-employee'),
    path('attendance/hr/monthly-report/', views.HRMonthlyReportAPIView.as_view(),
         name='attendance-hr-monthly-report'),
]
