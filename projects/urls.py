from django.urls import path
from . import views

app_name = "projects"

urlpatterns = [
    path("dm/project/create/", views.DMCreateProjectAPIView.as_view()),

    path("pm/project/<int:project_id>/module/create/",
         views.PMCreateModuleAPIView.as_view()),

    path("tl/module/<int:module_id>/task/create/",
         views.TLCreateTaskAPIView.as_view()),

    path("employee/task/<int:task_id>/subtask/create/",
         views.EmployeeCreateSubTaskAPIView.as_view()),

    path("project/<int:project_id>/status/",
         views.ProjectStatusUpdateAPIView.as_view()),

    path("module/<int:module_id>/status/",
         views.ModuleStatusUpdateAPIView.as_view()),

    path("task/<int:task_id>/status/", views.TaskStatusUpdateAPIView.as_view()),

    path("subtask/<int:subtask_id>/status/",
         views.SubTaskStatusUpdateAPIView.as_view()),

    path("dashboard/dm/", views.DMDashboardAPIView.as_view()),

    path("dashboard/pm/", views.PMDashboardAPIView.as_view()),

    path("dashboard/tl/", views.TLDashboardAPIView.as_view()),
]
