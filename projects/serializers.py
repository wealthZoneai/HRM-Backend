from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Project, ProjectModule, Task, SubTask


class ProjectSerializer(serializers.ModelSerializer):
    project_manager = serializers.SlugRelatedField(
        slug_field='username',
        queryset=get_user_model().objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Project
        fields = (
            "id",
            "name",
            "description",
            "delivery_manager",
            "project_manager",
            "status",
            "created_at",
        )
        read_only_fields = ("delivery_manager", "status")


class ProjectModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectModule
        fields = (
            "id",
            "project",
            "name",
            "description",
            "team_lead",
            "status",
        )
        read_only_fields = ("project", "status")


class TaskSerializer(serializers.ModelSerializer):
    assigned_date = serializers.DateField(required=False)

    class Meta:
        model = Task
        fields = (
            "id",
            "module",
            "title",
            "description",
            "assigned_to",
            "created_by",
            "status",
            "assigned_date",
            "due_date",
        )
        read_only_fields = ("module", "created_by", "status")



class SubTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTask
        fields = (
            "id",
            "task",
            "title",
            "description",
            "created_by",
            "status",
            "approved_by_tl",
        )
        read_only_fields = ("task", "created_by", "approved_by_tl", "status")



class ProjectStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=['in_progress', 'at_risk', 'completed', 'closed']
    )


class ModuleStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=['in_progress', 'blocked', 'completed', 'returned']
    )


class TaskStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=['review', 'rework', 'completed']
    )


class SubTaskStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=['in_progress', 'completed', 'rejected']
    )


class SubTaskReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTask
        fields = ('id', 'title', 'status', 'created_by', 'approved_by_tl')


class TaskReadSerializer(serializers.ModelSerializer):
    subtasks = SubTaskReadSerializer(many=True, read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ('id', 'title', 'status', 'assigned_to',
                  'created_by_name', 'assigned_date', 'due_date', 'subtasks')

    def get_created_by_name(self, obj):
        """Return the full name of the team lead who created the task"""
        user = obj.created_by
        if hasattr(user, 'first_name') and hasattr(user, 'last_name'):
            full_name = f"{user.first_name} {user.last_name}".strip()
            return full_name if full_name else user.username
        return user.username


class ModuleReadSerializer(serializers.ModelSerializer):
    tasks = TaskReadSerializer(many=True, read_only=True)

    class Meta:
        model = ProjectModule
        fields = ('id', 'name', 'status', 'team_lead', 'tasks')


class ProjectReadSerializer(serializers.ModelSerializer):
    modules = ModuleReadSerializer(many=True, read_only=True)

    project_manager = serializers.StringRelatedField()
    delivery_manager = serializers.StringRelatedField()

    class Meta:
        model = Project
        fields = ('id', 'name', 'description', 'status',
                  'project_manager', 'delivery_manager', 'created_at', 'modules')


class AssignPMSerializer(serializers.Serializer):
    project_manager = serializers.SlugRelatedField(
        slug_field='username',
        queryset=get_user_model().objects.all(),
        required=True
    )


class EmployeeProjectStatusSerializer(serializers.Serializer):
    project_id = serializers.IntegerField()
    project_name = serializers.CharField()
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    in_progress_tasks = serializers.IntegerField()
    todo_tasks = serializers.IntegerField()
