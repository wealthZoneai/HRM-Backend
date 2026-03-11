from rest_framework import serializers
from .models import (
    Project,
    TeamLead,
    Task,
    Risk,
    TimelineTask,
    TeamMember
)


# -----------------------------
# TEAM LEAD SERIALIZER
# -----------------------------
class TeamLeadSerializer(serializers.ModelSerializer):

    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = TeamLead
        fields = "__all__"


# -----------------------------
# PROJECT SERIALIZER
# -----------------------------
class ProjectSerializer(serializers.ModelSerializer):

    team_lead_name = serializers.CharField(
        source="team_lead.user.username",
        read_only=True
    )

    class Meta:
        model = Project
        fields = "__all__"


# -----------------------------
# TASK SERIALIZER
# -----------------------------
class TaskSerializer(serializers.ModelSerializer):

    project_name = serializers.CharField(
        source="project.name",
        read_only=True
    )

    assignee_name = serializers.CharField(
        source="assignee.username",
        read_only=True
    )

    class Meta:
        model = Task
        fields = "__all__"


# -----------------------------
# RISK SERIALIZER
# -----------------------------
class RiskSerializer(serializers.ModelSerializer):

    project_name = serializers.CharField(
        source="project.name",
        read_only=True
    )

    class Meta:
        model = Risk
        fields = "__all__"


# -----------------------------
# TIMELINE TASK SERIALIZER
# -----------------------------
class TimelineTaskSerializer(serializers.ModelSerializer):

    project_name = serializers.CharField(
        source="project.name",
        read_only=True
    )

    class Meta:
        model = TimelineTask
        fields = "__all__"


# -----------------------------
# PROJECT TIMELINE SERIALIZER
# -----------------------------
class ProjectTimelineSerializer(serializers.ModelSerializer):

    timeline_tasks = TimelineTaskSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "status",
            "deadline",
            "timeline_tasks"
        ]


# -----------------------------
# TEAM MEMBER SERIALIZER
# -----------------------------
class TeamMemberSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    class Meta:
        model = TeamMember
        fields = "__all__"