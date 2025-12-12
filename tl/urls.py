from django.urls import path
from . import views

app_name = "tl"

urlpatterns = [
    path("team/members/", views.TLTeamMembersAPIView.as_view(), name="team-members"),

    path("team/attendance/", views.TLTeamAttendanceAPIView.as_view(),
         name="team-attendance"),

    path("team/dashboard/", views.TLDashboardAPIView.as_view(),
         name="team-dashboard"),

    path("tl/list/", views.TeamLeadListAPIView.as_view(), name="tl-list"),

    path("leave/pending/", views.TLPendingLeaveAPIView.as_view(),
         name="leave-pending"),

    path("leave/<int:leave_id>/action/",
         views.TLApproveRejectLeaveAPIView.as_view(), name="leave-action"),

    path("calendar/create/", views.TLCreateEventAPIView.as_view(),
         name="calendar-create"),

    path("announcement/create/", views.tl_create_announcement,
         name="tl-create-announcement"),
]
