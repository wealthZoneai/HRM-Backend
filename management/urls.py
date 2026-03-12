from django.urls import path
from . import views
from .views import NewJoineesThisMonthAPIView

urlpatterns = [
#attendance and leaves
    path('admin/long-leave-dashboard/', views.admin_long_leave_dashboard),

    path('admin/total-employees/', views.ADMINTotalEmployeesAPIView.as_view(), name='admin-total-employees'),

    path('admin/on-leave/', views.ADMINOnLeaveAPIView.as_view(), name='admin-on-leave'),


    path('admin/pending-requests/', views.ADMINPendingRequestsAPIView.as_view(), name='admin-pending-requests'),

    path('admin/late-arrivals/', views.ADMINLateArrivalsAPIView.as_view(), name='admin-late-arrivals'),

    path('admin/leave-breakdown/', views.ADMINLeaveTypeBreakdownAPIView.as_view(), name='admin-leave-breakdown'),

    path('admin/employees-on-leave-dept-wise/',views.ADMINEmployeesOnLeaveDeptWiseAPIView.as_view(), name='admin-employees-on-leave-dept-wise'),

    path('admin/attendance-trend/',views.ADMINAttendanceTrendAPIView.as_view(),name='admin-attendance-trend'),

    path('admin/total-present/', views.total_present_api, name='admin-total-present'),

#total employees
    path("admin/total-employees/", views.TotalEmployeesAPIView.as_view(), name="ceo-total-employees"),
 
    path("admin/annual-growth/", views.AnnualGrowthAPIView.as_view(), name="ceo-annual-growth"),
 
    path("admin/new-joinees/", views.NewJoineesAPIView.as_view(), name="ceo-new-joinees"),
 
    path("admin/departments/", views.DepartmentHeadcountAPIView.as_view(), name="ceo-departments"),
 
    path("admin/monthly-employees/", views.MonthlyEmployeeChartAPIView.as_view(), name="ceo-monthly-employees"),
 
    path("admin/department-wise/", views.DepartmentEmployeeAPIView.as_view(), name="ceo-department-wise"  ),
    
    path("admin/new-joinees-this-month/",views.NewJoineesThisMonthAPIView.as_view(),name="new-joinees-this-month"),

#attritions

    path('admin/attrition/dashboard/',views.adminAttritionDashboardAPIView.as_view(),name='admin-attrition-dashboard'),

#reports
    path("admin/dashboard/", views.AdminDashboardAPIView.as_view(),name="admin-dashboard"),

    path("admin/clients/", views.AdminClientsAPIView.as_view(),name="admin-clients"),

    path("admin/projects/", views.AdminProjectsAPIView.as_view(),name="admin-projects"),

    path("admin/managers/", views.AdminManagersAPIView.as_view(),name="admin-managers"),

    path("admin/module-progress/", views.ModuleProgressAPIView.as_view(),name="module-progress"),

    path("admin/risk-alerts/", views.RiskAlertsAPIView.as_view(),name="risk-alerts"),

]

