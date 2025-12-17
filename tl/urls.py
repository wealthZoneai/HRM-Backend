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

    path("tl/calendar/create/", views.TLCreateEventAPIView.as_view(),
         name="calendar-create"),

    path('tl/calendar/<int:pk>/update/',
         views.TLCalendarUpdateAPIView.as_view(), name='tl_calendar_update'),

    path('tl/calendar/<int:pk>/delete/',
         views.TLCalendarDeleteAPIView.as_view(), name='tl_calendar_delete'),

    path("tl/announcement/create/", views.tl_create_announcement,
         name="tl-create-announcement"),

    path("tl/announcement/<int:pk>/update/", views.tl_update_announcement,
         name="tl-update-announcement"),

    path("tl/announcement/<int:pk>/delete/", views.tl_delete_announcement,
         name="tl-delete-announcement"),
]
