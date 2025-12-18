# tl/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum
from django.utils import timezone
from django.contrib.auth import get_user_model
from emp.models import EmployeeProfile, LeaveRequest, Attendance, CalendarEvent, Notification
from .models import TLAnnouncement
from emp.permissions import IsHROrManagement
from emp.serializers import LeaveRequestSerializer, AttendanceReadSerializer, CalendarEventSerializer
from .serializers import TeamMemberSerializer, TLAnnouncementSerializer
from .permissions import IsTL
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db import IntegrityError

User = get_user_model()


class TLTeamMembersAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsTL]
    serializer_class = TeamMemberSerializer

    def get_queryset(self):

        return EmployeeProfile.objects.filter(team_lead=self.request.user)


class TLPendingLeaveAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsTL]
    serializer_class = LeaveRequestSerializer

    def get_queryset(self):
        return LeaveRequest.objects.filter(
            tl=self.request.user,
            status="applied"
        ).select_related("profile")


class TLApproveRejectLeaveAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTL]

    def post(self, request, leave_id):
        leave = get_object_or_404(LeaveRequest, id=leave_id)

        # If leave does not require TL approval
        if leave.tl is None:
            return Response(
                {"detail": "This leave does not require TL approval."},
                status=400
            )

        if leave.tl != request.user:
            return Response(
                {"detail": "Not your team member"},
                status=403
            )

        action = request.data.get("action")
        remarks = request.data.get("remarks", "")

        if action == "approve":
            leave.apply_tl_approval(
                request.user, approve=True, remarks=remarks)
            return Response({"detail": "TL approved leave."})

        leave.apply_tl_approval(request.user, approve=False, remarks=remarks)
        return Response({"detail": "TL rejected leave."})


class TLTeamAttendanceAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsTL]
    serializer_class = AttendanceReadSerializer

    def get_queryset(self):
        month = self.request.query_params.get("month")
        team = EmployeeProfile.objects.filter(
            team_lead=self.request.user).values_list("user", flat=True)
        qs = Attendance.objects.filter(user__in=team)

        if not month:
            return qs.order_by("-date")

        try:
            y, m = map(int, month.split("-"))
        except (ValueError, AttributeError):
            return qs.order_by("-date")

        qs = qs.filter(date__year=y, date__month=m)
        return qs.order_by("-date")


class TLCreateEventAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTL]

    def post(self, request):
        title = request.data.get("title")
        description = request.data.get("description", "")
        date = request.data.get("date")
        start_time = request.data.get("start_time")
        end_time = request.data.get("end_time")

        if not title or not date or not start_time or not end_time:
            return Response({"detail": "Missing required fields."}, status=400)

        try:
            event = CalendarEvent.objects.create(
                title=title,
                description=description,
                event_type="meeting",
                date=date,
                start_time=start_time,
                end_time=end_time,
                created_by=request.user,
                visible_to_tl_hr=True,
            )
        except Exception as e:
            return Response({"detail": "Invalid event data", "error": str(e)}, status=400)

        return Response(CalendarEventSerializer(event).data, status=201)


class TLCalendarUpdateAPIView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsTL]
    serializer_class = CalendarEventSerializer

    def get_queryset(self):
        return CalendarEvent.objects.filter(created_by=self.request.user)


class TLCalendarDeleteAPIView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsTL]

    def get_queryset(self):
        return CalendarEvent.objects.filter(created_by=self.request.user)


class TLDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTL]

    def get(self, request):
        user = request.user

        team_members = EmployeeProfile.objects.filter(team_lead=user)

        team_count = team_members.count()

        pending_leaves = LeaveRequest.objects.filter(
            tl=user,
            status="applied"
        ).count()

        today = timezone.localdate()
        y, m = today.year, today.month
        attendance_qs = Attendance.objects.filter(
            user__in=team_members.values_list("user", flat=True),
            date__year=y,
            date__month=m
        )

        total_present = attendance_qs.count()
        total_seconds = attendance_qs.aggregate(
            total=Sum("duration_seconds"))["total"] or 0

        meetings = CalendarEvent.objects.filter(
            event_type="meeting",
            created_by=user
        ).order_by("-date")[:5]

        meeting_data = CalendarEventSerializer(meetings, many=True).data

        return Response({
            "team_count": team_count,
            "pending_leave_requests": pending_leaves,
            "attendance_summary": {
                "present_days": total_present,
                # duration_time stored in seconds → convert to hours
                "total_hours": round(total_seconds / 3600, 2)
            },
            "recent_meetings": meeting_data
        })


class TeamLeadListAPIView(APIView):
    permission_classes = [IsHROrManagement]

    def get(self, request):

        dept = request.query_params.get('department')

        qs = User.objects.filter(
            role__iexact='tl', employeeprofile__isnull=False)

        if dept:
            qs = qs.filter(employeeprofile__department__iexact=dept)

        profiles = EmployeeProfile.objects.filter(user__in=qs)
        ser = TeamMemberSerializer(profiles, many=True)
        return Response(ser.data)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsTL])
def tl_create_announcement(request):
    serializer = TLAnnouncementSerializer(data=request.data)

    if serializer.is_valid():
        try:
            announcement = serializer.save(
                created_by=request.user,
                created_role='TL'
            )
        except IntegrityError:
            return Response({
                "success": False,
                "errors": "An announcement already exists at this date and time."
            }, status=400)

        employees = EmployeeProfile.objects.filter(
            team_lead=request.user,
            is_active=True
        ).select_related('user')

        Notification.objects.bulk_create([
            Notification(
                to_user=emp.user,
                title=announcement.title,
                body=announcement.description,
                notif_type='announcement'
            )
            for emp in employees
        ])

        return Response({
            "success": True,
            "message": "Announcement sent to team"
        })

    return Response(serializer.errors, status=400)


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsTL])
def tl_update_announcement(request, pk):
    try:
        announcement = TLAnnouncement.objects.get(
            pk=pk,
            created_by=request.user   # TL can update only own announcements
        )
    except TLAnnouncement.DoesNotExist:
        return Response(
            {"success": False, "message": "Announcement not found"},
            status=404
        )

    serializer = TLAnnouncementSerializer(
        announcement, data=request.data, partial=True
    )

    if serializer.is_valid():
        serializer.save()

        return Response({
            "success": True,
            "message": "Announcement updated successfully",
            "data": serializer.data
        })

    return Response(serializer.errors, status=400)


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsTL])
def tl_delete_announcement(request, pk):
    try:
        announcement = TLAnnouncement.objects.get(
            pk=pk,
            created_by=request.user
        )
    except TLAnnouncement.DoesNotExist:
        return Response(
            {"success": False, "message": "Announcement not found"},
            status=404
        )

    announcement.delete()

    return Response({
        "success": True,
        "message": "Announcement deleted successfully"
    })


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsTL])
def tl_create_announcement(request):
    serializer = TLAnnouncementSerializer(data=request.data)

    if serializer.is_valid():
        announcement = serializer.save(
            created_by=request.user,
            created_role='TL'
        )

        if announcement.show_in_calendar:
            CalendarEvent.objects.create(
                title=announcement.title,
                description=announcement.description,
                event_type="announcement",
                date=announcement.date,
                start_time=announcement.time,
                created_by=request.user,
                visible_to_tl_hr=True,
                extra={
                    "tl_announcement_id": announcement.id,
                    "source": "TL"
                }
            )

        employees = EmployeeProfile.objects.filter(
            team_lead=request.user,
            is_active=True
        ).select_related('user')

        Notification.objects.bulk_create([
            Notification(
                to_user=emp.user,
                title=announcement.title,
                body=announcement.description,
                notif_type="announcement"
            )
            for emp in employees
        ])

        return Response({
            "success": True,
            "message": "TL announcement created"
        }, status=201)

    return Response(serializer.errors, status=400)
