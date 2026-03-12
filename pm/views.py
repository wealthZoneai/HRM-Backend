from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Project, TeamLead, Task, Risk, TeamMember
from .serializers import ProjectSerializer, TaskSerializer, RiskSerializer, TeamMemberSerializer, ProjectTimelineSerializer


# -------------------------
# All Projects
# -------------------------
@api_view(['GET'])
def all_projects(request):

    projects = Project.objects.all()
    serializer = ProjectSerializer(projects, many=True)

    return Response(serializer.data)


# -------------------------
# New Projects
# -------------------------
@api_view(['GET'])
def new_projects(request):

    projects = Project.objects.filter(status='new')
    serializer = ProjectSerializer(projects, many=True)

    return Response(serializer.data)


# -------------------------
# Inprogress Projects
# -------------------------
@api_view(['GET'])
def inprogress_projects(request):

    projects = Project.objects.filter(status='inprogress')
    serializer = ProjectSerializer(projects, many=True)

    return Response(serializer.data)


# -------------------------
# Completed Projects
# -------------------------
@api_view(['GET'])
def completed_projects(request):

    projects = Project.objects.filter(status='completed')
    serializer = ProjectSerializer(projects, many=True)

    return Response(serializer.data)


# -------------------------
# Project Details
# -------------------------
@api_view(['GET'])
def project_details(request, project_id):

    project = Project.objects.get(id=project_id)
    serializer = ProjectSerializer(project)

    return Response(serializer.data)


# -------------------------
# Assign Team Lead
# -------------------------
@api_view(['POST'])
def assign_team_lead(request, project_id):

    lead_id = request.data.get("team_lead_id")

    project = Project.objects.get(id=project_id)
    lead = TeamLead.objects.get(id=lead_id)

    project.team_lead = lead
    project.status = "inprogress"
    project.save()

    return Response({"message": "Team lead assigned"})


# -------------------------
# Workboard
# -------------------------
@api_view(['GET'])
def workboard(request):

    tasks = Task.objects.all()

    todo = tasks.filter(status="todo")
    inprogress = tasks.filter(status="inprogress")
    done = tasks.filter(status="done")

    data = {
        "todo": TaskSerializer(todo, many=True).data,
        "inprogress": TaskSerializer(inprogress, many=True).data,
        "done": TaskSerializer(done, many=True).data
    }

    return Response(data)


# -------------------------
# Timeline
# -------------------------
@api_view(['GET'])
def pm_timeline(request):

    projects = Project.objects.all()
    serializer = ProjectTimelineSerializer(projects, many=True)

    return Response(serializer.data)


# -------------------------
# PM Dashboard
# -------------------------
@api_view(['GET'])
def pm_dashboard(request):

    active_projects = Project.objects.filter(status="inprogress").count()
    total_tasks = Task.objects.count()
    completed_tasks = Task.objects.filter(status="done").count()
    team_members = TeamMember.objects.count()

    projects = Project.objects.all()
    tasks = Task.objects.all()[:5]
    risks = Risk.objects.all()[:5]

    data = {
        "active_projects": active_projects,
        "tasks_completed": completed_tasks,
        "total_tasks": total_tasks,
        "team_members": team_members,
        "projects": ProjectSerializer(projects, many=True).data,
        "recent_tasks": TaskSerializer(tasks, many=True).data,
        "risks": RiskSerializer(risks, many=True).data
    }

    return Response(data)


# -------------------------
# Team Members
# -------------------------
@api_view(['GET'])
def all_team_members(request):

    members = TeamMember.objects.all()
    serializer = TeamMemberSerializer(members, many=True)

    return Response(serializer.data)