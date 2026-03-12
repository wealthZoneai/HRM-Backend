from django.urls import path
from . import views


urlpatterns = [

    # -------------------------
    # Project List Filters
    # -------------------------
    path("projects/all/", views.all_projects, name="all-projects"),
    path("projects/new/", views.new_projects, name="new-projects"),
    path("projects/inprogress/", views.inprogress_projects, name="inprogress-projects"),
    path("projects/completed/", views.completed_projects, name="completed-projects"),

    # -------------------------
    # Project Details
    # -------------------------
    path("projects/detail/<int:project_id>/", views.project_details, name="project-details"),

    # -------------------------
    # Assign Team Lead
    # -------------------------
    path("projects/assign-lead/<int:project_id>/", views.assign_team_lead, name="assign-team-lead"),

    # -------------------------
    # Workboard
    # -------------------------
    path("workboard/", views.workboard, name="workboard"),

    # -------------------------
    # Timeline
    # -------------------------
    path("timeline/", views.pm_timeline, name="pm-timeline"),

    # -------------------------
    # PM Dashboard
    # -------------------------
    path("pm-dashboard/", views.pm_dashboard, name="pm-dashboard"),

    # -------------------------
    # Team Members
    # -------------------------
    path("team-members/", views.all_team_members, name="all-team-members"),

]