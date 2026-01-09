from rest_framework import serializers
from .models import Project, ProjectModule, Task, SubTask


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"
        read_only_fields = ('delivery_manager', 'status')


class ProjectModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectModule
        fields = "__all__"


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"
        read_only_fields = ('created_by', 'status')


class SubTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTask
        fields = "__all__"
        read_only_fields = ('created_by', 'approved_by_tl', 'status')


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

    class Meta:
        model = Task
        fields = ('id', 'title', 'status', 'assigned_to', 'subtasks')


class ModuleReadSerializer(serializers.ModelSerializer):
    tasks = TaskReadSerializer(many=True, read_only=True)

    class Meta:
        model = ProjectModule
        fields = ('id', 'name', 'status', 'team_lead', 'tasks')


class ProjectReadSerializer(serializers.ModelSerializer):
    modules = ModuleReadSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ('id', 'name', 'status', 'project_manager', 'modules')
