from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Project, ProjectModule, Task, SubTask, ProjectAudit
from emp.models import Notification
from .serializers import (ProjectStatusUpdateSerializer, ModuleStatusUpdateSerializer,
                          TaskStatusUpdateSerializer, SubTaskStatusUpdateSerializer,
                          ProjectReadSerializer)

from .models import Project, ProjectModule, Task, SubTask
from .serializers import (
    ProjectSerializer, ProjectModuleSerializer,
    TaskSerializer, SubTaskSerializer)
from .permissions import IsDM, IsPM, IsTL, IsEmployee
from emp.permissions import IsHROrManagement


class DMCreateProjectAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDM]

    def post(self, request):
        ser = ProjectSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        project = ser.save(delivery_manager=request.user)
        return Response(ProjectSerializer(project).data, status=201)


class PMCreateModuleAPIView(APIView):
    permission_classes = [IsAuthenticated, IsPM]

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        ser = ProjectModuleSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        module = ser.save(project=project)
        return Response(ProjectModuleSerializer(module).data, status=201)


class TLCreateTaskAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTL]

    def post(self, request, module_id):
        module = get_object_or_404(ProjectModule, id=module_id)
        ser = TaskSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        task = ser.save(
            module=module,
            created_by=request.user
        )
        return Response(TaskSerializer(task).data, status=201)


class EmployeeCreateSubTaskAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)

        if task.assigned_to != request.user:
            return Response(
                {"detail": "You can create subtasks only for your own tasks."},
                status=403
            )

        ser = SubTaskSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        subtask = ser.save(task=task, created_by=request.user)
        return Response(SubTaskSerializer(subtask).data, status=201)


class ProjectStatusUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)

        serializer = ProjectStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        user_role = request.user.role

        if new_status in ('completed', 'closed') and user_role != 'management':
            return Response({"detail": "Only Delivery Manager can do this"}, status=403)

        if new_status in ('in_progress', 'at_risk') and user_role != 'pm':
            return Response({"detail": "Only Project Manager can do this"}, status=403)

        old_status = project.status

        project.status = new_status
        project.save(update_fields=['status'])

        ProjectAudit.objects.create(
            project=project,
            actor=request.user,
            action='project_status',
            old_value=old_status,
            new_value=new_status
        )

        return Response({
            "project_id": project.id,
            "old_status": old_status,
            "new_status": new_status
        }, status=200)


class ModuleStatusUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, module_id):
        module = get_object_or_404(ProjectModule, id=module_id)

        serializer = ModuleStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']

        if new_status in ('in_progress', 'blocked', 'completed') and request.user.role != 'tl':
            return Response({"detail": "Only TL allowed"}, status=403)

        if new_status == 'returned' and request.user.role != 'pm':
            return Response({"detail": "Only PM allowed"}, status=403)

        old_status = module.status

        module.status = new_status
        module.save(update_fields=['status'])

        ProjectAudit.objects.create(
            project=module.project,
            actor=request.user,
            action='module_status',
            old_value=old_status,
            new_value=new_status
        )

        return Response({
            "module_id": module.id,
            "old_status": old_status,
            "new_status": new_status
        })


class TaskStatusUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)

        serializer = TaskStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']

        if new_status == 'review' and request.user != task.assigned_to:
            return Response({"detail": "Only assignee can submit for review"}, status=403)

        if new_status in ('rework', 'completed') and request.user.role != 'tl':
            return Response({"detail": "Only TL allowed"}, status=403)

        old_status = task.status

        task.status = new_status
        task.save(update_fields=['status'])

        ProjectAudit.objects.create(
            project=task.module.project,
            actor=request.user,
            action='task_status',
            old_value=old_status,
            new_value=new_status
        )

        return Response({
            "task_id": task.id,
            "old_status": old_status,
            "new_status": new_status
        })


class SubTaskStatusUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, subtask_id):
        subtask = get_object_or_404(SubTask, id=subtask_id)
        ser = SubTaskStatusUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        new_status = ser.validated_data['status']

        if request.user.role == 'tl':
            subtask.status = new_status
            subtask.approved_by_tl = request.user

        elif request.user == subtask.created_by:
            if new_status != 'in_progress':
                return Response({"detail": "Invalid action"}, status=403)
            subtask.status = new_status
        else:
            return Response({"detail": "Not allowed"}, status=403)

        subtask.save(update_fields=['status', 'approved_by_tl'])

        Notification.objects.create(
            to_user=subtask.created_by,
            title=f"Subtask update: {subtask.title}",
            body=f"Subtask marked {new_status}",
            notif_type="project"
        )

        return Response({"status": subtask.status})


class DMDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDM]

    def get(self, request):
        qs = Project.objects.all()

        return Response({
            "total_projects": qs.count(),
            "in_progress": qs.filter(status='in_progress').count(),
            "at_risk": qs.filter(status='at_risk').count(),
            "completed": qs.filter(status='completed').count(),
        })


class PMDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsPM]

    def get(self, request):
        modules = ProjectModule.objects.filter(
            project__project_manager=request.user
        )

        return Response({
            "total_modules": modules.count(),
            "blocked": modules.filter(status='blocked').count(),
            "completed": modules.filter(status='completed').count(),
        })


class TLDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTL]

    def get(self, request):
        tasks = Task.objects.filter(created_by=request.user)

        return Response({
            "assigned_tasks": tasks.count(),
            "pending_review": tasks.filter(status='review').count(),
            "completed": tasks.filter(status='completed').count(),
        })


class ProjectHierarchyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)

        # Visibility rules
        user = request.user
        if user.role == 'employee':
            if not Task.objects.filter(
                module__project=project,
                assigned_to=user
            ).exists():
                return Response({"detail": "Not allowed"}, status=403)

        serializer = ProjectReadSerializer(project)
        return Response(serializer.data)


class HRProjectAnalyticsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsHROrManagement]

    def get(self, request):
        return Response({
            "projects_total": Project.objects.count(),
            "in_progress": Project.objects.filter(status='in_progress').count(),
            "at_risk": Project.objects.filter(status='at_risk').count(),
            "completed": Project.objects.filter(status='completed').count(),
        })
