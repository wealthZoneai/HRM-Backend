from rest_framework import serializers
from .models import LongLeave


class LongLeaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = LongLeave
        fields = '__all__'


from rest_framework import serializers
from emp.models import EmployeeProfile
 
 
class NewJoineeSerializer(serializers.ModelSerializer):
 
    class Meta:
        model = EmployeeProfile
        fields = [
            "id",
            "first_name",
            "last_name",
            "department",
            "designation",
            "joining_date"
        ]
        
class NewJoineesMonthSerializer(serializers.ModelSerializer):
 
    name = serializers.SerializerMethodField()
 
    class Meta:
        model = EmployeeProfile
        fields = [
            "emp_id",
            "name",
            "department",
            "designation",
            "date_of_joining"
        ]
 
    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
#-------
#Reports
#-------


from rest_framework import serializers
from .models import Project, ModuleProgress, RiskAlert
class AdminDashboardSerializer(serializers.ModelSerializer):

    client = serializers.CharField(source="client.name")
    delivery_manager = serializers.CharField(source="delivery.name")

    class Meta:
        model = Project
        fields = [
            "client",
            "project",
            "delivery_manager",
            "start_date",
            "end_date",
            "completion",
            "status"
        ]

class ModuleProgressSerializer(serializers.ModelSerializer):

    project_name = serializers.CharField(source="project.project")

    class Meta:
        model = ModuleProgress
        fields = ["project_name", "module_name", "progress"]

class RiskAlertSerializer(serializers.ModelSerializer):

    project_name = serializers.CharField(source="project.project")

    class Meta:
        model = RiskAlert
        fields = ["project_name", "message", "level"]