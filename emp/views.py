# emp/views.py
from .permissions import IsTLOnly, IsHROrManagement, IsTLorHRorOwner
from django.utils.dateparse import parse_date, parse_datetime
from urllib.parse import unquote
from .serializers import (
    TimesheetEntrySerializer,
    DailyTimesheetUpdateSerializer,
    EmployeeCreateSerializer,
    EmployeeProfileReadSerializer,
    NotificationSerializer,
    TodayAttendanceSerializer,
)
from tl.serializers import TLAnnouncementSerializer
from .models import TimesheetEntry, TimesheetDay, EmployeeProfile, Notification, Attendance
from tl.models import TLAnnouncement
from django.db import transaction
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404, render
from django.db.models import Sum, Count, Q
import calendar
from datetime import timedelta, time
from . import models, serializers
from django.contrib.auth import get_user_model
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from hr.models import Announcement
from hr.serializers import AnnouncementSerializer
from datetime import datetime, time
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import FileResponse, Http404
from django.contrib.auth.decorators import login_required
import mimetypes


User = get_user_model()


def _employee_display_name(prof):
    """Best-effort employee display name (safe fallbacks)."""
    try:
        fn = getattr(prof, "full_name", None)
        if callable(fn):
            name = fn()
            if name:
                return name
    except Exception:
        pass

    first = getattr(prof, "first_name", "") or ""
    last = getattr(prof, "last_name", "") or ""
    combined = " ".join(p for p in (first.strip(), last.strip()) if p).strip()
    if combined:
        return combined

    user = getattr(prof, "user", None)
    if user:
        try:
            guf = getattr(user, "get_full_name", None)
            if callable(guf):
                u_name = guf()
                if u_name:
                    return u_name
        except Exception:
            pass

        if getattr(user, "username", None):
            return user.username
        if getattr(user, "email", None):
            return user.email

    return getattr(prof, "emp_id", "")


class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        prof = request.user.employeeprofile
        return Response(serializers.EmployeeProfileReadSerializer(prof).data)


class ProtectedEmployeeDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, emp_id, doc_field):
        """
        emp_id     -> EmployeeProfile.emp_id
        doc_field  -> model field name (aadhaar_front_image, pan_back_image, etc)
        """

        try:
            profile = EmployeeProfile.objects.get(emp_id=emp_id)
        except EmployeeProfile.DoesNotExist:
            raise Http404("Employee not found")

        # --- ACCESS CONTROL ---
        user = request.user
        if user.role not in ("hr", "management") and profile.user != user:
            raise Http404("Not allowed")

        # --- VALID FIELDS (whitelist) ---
        allowed_fields = {
            "aadhaar_front_image",
            "aadhaar_back_image",
            "pan_front_image",
            "pan_back_image",
            "passport_front_image",
            "passport_back_image",
        }

        if doc_field not in allowed_fields:
            raise Http404("Invalid document")

        file = getattr(profile, doc_field, None)
        if not file:
            raise Http404("File not found")

        content_type, _ = mimetypes.guess_type(file.path)

        response = FileResponse(
            open(file.path, "rb"),
            content_type=content_type or "application/octet-stream"
        )

        # ✅ FORCE INLINE VIEW (not download)
        response["Content-Disposition"] = f'inline; filename="{file.name}"'

        return response


class UpdateContactView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        prof = request.user.employeeprofile
        serializer = serializers.EmployeeContactUpdateSerializer(
            prof,
            data=request.data,
            partial=True,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UpdateIdentificationView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        prof = request.user.employeeprofile
        serializer = serializers.EmployeeIdentificationSerializer(
            prof,
            data=request.data,
            partial=True,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class MyNotificationsList(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.NotificationSerializer

    def get_queryset(self):
        q = models.Notification.objects.filter(to_user=self.request.user)
        if self.request.query_params.get('unread') in ('true', '1', 'True'):
            q = q.filter(is_read=False)
        return q

    def get(self, request, format=None):
        notifications = Notification.objects.filter(
            to_user=request.user).order_by('-created_at')
        serializer = NotificationSerializer(notifications, many=True)
        return Response({
            "success": True,
            "data": serializer.data
        })


class MarkNotificationsRead(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ids = request.data.get('ids', [])
        models.Notification.objects.filter(
            id__in=ids, to_user=request.user).update(is_read=True)
        return Response({"marked": len(ids)})


class DashboardSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.localdate()
        att = models.Attendance.objects.filter(user=user, date=today).first()
        att_ser = serializers.AttendanceReadSerializer(
            att).data if att else None

        month_q = request.query_params.get('month')
        if month_q:
            y, m = map(int, month_q.split('-'))
        else:
            d = timezone.localdate()
            y, m = d.year, d.month

        qs = models.Attendance.objects.filter(
            user=user, date__year=y, date__month=m, status='completed')
        days_present = qs.count()
        total_seconds = qs.aggregate(total=Sum('duration_seconds'))[
            'total'] or 0
        monthly_summary = {'year': y, 'month': m, 'days_present': days_present, 'hours': round(
            total_seconds/3600.0, 2)}

        project_status = []

        announcements = models.Notification.objects.filter(
            to_user=user).order_by('-created_at')[:5]
        ann_ser = serializers.NotificationSerializer(
            announcements, many=True).data

        leave_counts = models.LeaveRequest.objects.filter(
            profile=user.employeeprofile).values('status').annotate(c=Count('id'))
        leave_summary = {row['status']: row['c'] for row in leave_counts}

        upcoming = models.CalendarEvent.objects.filter(
            event_type='holiday', date__gte=today).order_by('date')[:10]
        up_ser = serializers.CalendarEventSerializer(upcoming, many=True).data

        return Response({
            'attendance_today': att_ser,
            'monthly_summary': monthly_summary,
            'project_status': project_status,
            'announcements': ann_ser,
            'leave_summary': leave_summary,
            'upcoming_holidays': up_ser,
        })


class ClockInAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        today = timezone.localdate()

        if models.Attendance.objects.filter(user=user, date=today).exists():
            return Response({"detail": "Attendance for today already exists."}, status=400)
        att = models.Attendance.objects.create(user=user, date=today, clock_in=timezone.now(
        ), status='working')
        return Response(serializers.AttendanceReadSerializer(att).data, status=201)


class ClockOutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        today = timezone.localdate()

        att = models.Attendance.objects.filter(
            user=user,
            date=today
        ).first()

        if not att:
            return Response(
                {"detail": "No clock-in found for today."},
                status=400
            )

        if att.clock_out:
            return Response(
                {"detail": "Already clocked out."},
                status=400
            )

        att.clock_out = timezone.now()
        att.compute_duration_and_overtime()
        att.save()

        data = serializers.AttendanceReadSerializer(att).data

        return Response(data, status=200)


class MyAttendanceDaysAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.AttendanceReadSerializer

    def get_queryset(self):
        user = self.request.user
        month = self.request.query_params.get('month')
        if month:
            y, m = map(int, month.split('-'))
            return models.Attendance.objects.filter(user=user, date__year=y, date__month=m).order_by('-date')
        else:
            return models.Attendance.objects.filter(user=user).order_by('-date')[:30]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        total_seconds = 0
        overtime_seconds = 0
        monthly_late_count = 0

        late_time_limit = time(9, 45)
        regular_work_seconds = 9 * 60 * 60

        # -------- Monthly Calculations --------
        for att in queryset:
            worked_seconds = 0

            # ✅ Total hours = sum of duration_time
            if att.clock_in and att.clock_out and att.duration_time:
                worked_seconds = att.duration_time.total_seconds()
                total_seconds += worked_seconds

                # ✅ Overtime after 9 hours
            if worked_seconds > regular_work_seconds:
                overtime_seconds += (worked_seconds - regular_work_seconds)

            # ✅ Late arrivals (after 09:30 AM)
            if att.clock_in:
                clock_in_time = att.clock_in.astimezone().time()
                if clock_in_time > late_time_limit:
                    monthly_late_count += 1

        total_hours_str = self.format_time(total_seconds)
        overtime_str = self.format_time(overtime_seconds)

        # -------- Serialize daily records --------
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data

        # -------- Inject monthly values (KEEP SAME FORMAT) --------
        for record in data:
            record["total_hours"] = total_hours_str
            record["overtime"] = overtime_str
            record["late_arrivals"] = monthly_late_count

        return Response(data)

    def format_time(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{int(hours):02d}:{int(minutes):02d}"


class TodayAttendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.localdate()
        qs = Attendance.objects.filter(date=today)

        if user.role == "employee":
            qs = qs.filter(user=user)

        elif user.role in ['tl', 'hr']:
            qs = qs.filter(
                Q(user=user) | Q(user__role="employee")
            )

        else:
            return Response(
                {"detail": "Unauthorized"},
                status=403
            )

        qs = qs.select_related("user").order_by("user__username")

        serializer = TodayAttendanceSerializer(qs, many=True)
        return Response(serializer.data, status=200)


class CalendarEventsAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.CalendarEventSerializer

    def get_queryset(self):
        year = int(self.request.query_params.get(
            'year', timezone.localdate().year))
        month = int(self.request.query_params.get(
            'month', timezone.localdate().month))
        q = models.CalendarEvent.objects.filter(
            date__year=year, date__month=month).order_by('date')
        return q


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def emp_all_announcements(request):
    announcements = Announcement.objects.all().order_by('-date')
    serializer = AnnouncementSerializer(announcements, many=True)
    return Response({
        "success": True,
        "data": serializer.data
    })


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def emp_notifications(request):
    notifications = Notification.objects.filter(
        to_user=request.user
    ).order_by('-created_at')

    serializer = NotificationSerializer(notifications, many=True)
    return Response({
        "success": True,
        "data": serializer.data
    })


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def mark_notifications_read(request):
    Notification.objects.filter(
        to_user=request.user,
        is_read=False
    ).update(is_read=True)

    return Response({
        "success": True,
        "message": "All notifications marked as read"
    })


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def emp_tl_announcements(request):
    profile = EmployeeProfile.objects.get(user=request.user)

    if not profile.team_lead:
        return Response({
            "success": True,
            "data": []
        })

    announcements = TLAnnouncement.objects.filter(
        created_by=profile.team_lead
    ).order_by('-date')

    serializer = TLAnnouncementSerializer(announcements, many=True)

    return Response({
        "success": True,
        "data": serializer.data
    })


class MySalaryDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        prof = request.user.employeeprofile
        try:
            es = prof.salary
            ser = serializers.EmployeeSalarySerializer(es).data
        except models.EmployeeSalary.DoesNotExist:
            ser = None
        return Response({'salary': ser})


class MyPayslipsAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.PayslipSerializer

    def get_queryset(self):
        prof = self.request.user.employeeprofile
        return models.Payslip.objects.filter(profile=prof).order_by('-year', '-month')


class PayslipDownloadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, year, month):
        prof = request.user.employeeprofile
        payslip = get_object_or_404(
            models.Payslip, profile=prof, year=year, month=month)

        return Response({'download_url': f'/media/payslips/{prof.emp_id}-{year}-{month}.pdf', 'payslip': serializers.PayslipSerializer(payslip).data})


class MyLeaveBalancesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        prof = request.user.employeeprofile
        balances = models.LeaveBalance.objects.filter(profile=prof)
        return Response(serializers.LeaveBalanceSerializer(balances, many=True).data)


class MyLeaveRequestsAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.LeaveRequestSerializer

    def get_queryset(self):
        return models.LeaveRequest.objects.filter(profile=self.request.user.employeeprofile)


class LeaveApplyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = serializers.LeaveApplySerializer(
            data=request.data,
            context={'request': request}
        )
        ser.is_valid(raise_exception=True)

        prof = request.user.employeeprofile
        start = ser.validated_data['start_date']
        end = ser.validated_data['end_date']

        existing_leave = models.LeaveRequest.objects.filter(
            profile=prof).exclude(status__in=['rejected', 'cancelled']).filter(
            start_date__lte=end, end_date__gte=start)

        if existing_leave.exists():
            return Response(
                {
                    "detail": (
                        "You already have a leave applied ",
                        "that overlaps with the selected date(s)."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.user.role == 'tl':
            route_direct_to_hr = True
            actionable_tl = None
        else:
            route_direct_to_hr = False
            actionable_tl = None

        if not route_direct_to_hr:
            primary_tl = getattr(prof, 'team_lead', None)
            if primary_tl and not getattr(primary_tl, 'is_active', True):
                primary_tl = None
            actionable_tl = primary_tl

            if not primary_tl:

                route_direct_to_hr = True
            else:

                tl_profile = getattr(primary_tl, 'employeeprofile', None)
                if tl_profile and tl_profile.is_on_leave(start, end):

                    fallback_tls = (
                        get_user_model()
                        .objects.filter(
                            role='tl',
                            employeeprofile__department=prof.department,
                            is_active=True
                        )
                        .exclude(id=primary_tl.id)
                        .select_related('employeeprofile')
                    )

                    found_replacement = False
                    for tl_user in fallback_tls:
                        if not tl_user.employeeprofile.is_on_leave(start, end):
                            actionable_tl = tl_user
                            found_replacement = True
                            break

                    if not found_replacement:
                        route_direct_to_hr = True

        duration_days = ser.validated_data.get('calculated_days')
        if duration_days is None:
            duration_days = (end - start).days + 1

        if route_direct_to_hr:
            tl_user = None
            initial_status = 'tl_approved'
        else:
            tl_user = actionable_tl
            initial_status = "applied" if prof.team_lead else "tl_approved"

        lr = models.LeaveRequest.objects.create(
            profile=prof,
            leave_type=ser.validated_data['normalized_leave_type'],
            start_date=start,
            end_date=end,
            days=duration_days,
            reason=ser.validated_data.get('reason', ''),
            status=initial_status,
            tl=tl_user,
        )

        hr_users = User.objects.filter(
            role__iexact="hr", is_active=True)

        Notification.objects.bulk_create([
            Notification(
                to_user=hr_user,
                title="New Leave Request",
                body=f"{prof.full_name()} applied for leave",
                notif_type="leave",
                extra={"leave_id": lr.id}
            )
            for hr_user in hr_users
        ])

        if not route_direct_to_hr and actionable_tl:
            models.Notification.objects.create(
                to_user=actionable_tl,
                title=f"Leave request from {prof.full_name()}",
                body=f"{prof.full_name()} applied for {lr.leave_type} "
                f"from {lr.start_date} to {lr.end_date}.",
                notif_type='leave',
                extra={'leave_request_id': lr.id}
            )
        return Response({
            "id": lr.id,
            "name": prof.full_name(),
            "emp_id": prof.emp_id,
            "role": request.user.role,
            "leave_type": lr.leave_type,
            "start_date": lr.start_date,
            "end_date": lr.end_date,
            "duration": lr.days,
            "reason": lr.reason,
            "status": lr.status
        }, status=201)


class HRCreateEmployeeAPIView(APIView):
    permission_classes = [IsAuthenticated, IsHROrManagement]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        data = {}

        for key, value in request.data.items():
            if key in ["contact", "job", "bank", "identification"]:

                try:
                    data[key] = json.loads(value) if isinstance(
                        value, str) else value
                except Exception:
                    data[key] = value
            else:
                data[key] = value

        for key, file_obj in request.FILES.items():

            if key.startswith("contact."):
                field = key.split("contact.")[1]
                if "contact" not in data or not isinstance(data["contact"], dict):
                    data["contact"] = {}
                data["contact"][field] = file_obj

            elif key.startswith("job."):
                field = key.split("job.")[1]
                if "job" not in data or not isinstance(data["job"], dict):
                    data["job"] = {}
                data["job"][field] = file_obj

            elif key.startswith("identification."):
                field = key.split("identification.")[1]
                if "identification" not in data or not isinstance(data["identification"], dict):
                    data["identification"] = {}
                data["identification"][field] = file_obj

            else:
                data[key] = file_obj

        serializer = EmployeeCreateSerializer(
            data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user, profile = serializer.save()
        return Response(EmployeeProfileReadSerializer(profile).data, status=status.HTTP_201_CREATED)


class MySensitiveDetailsAPIView(APIView):
    """
    TEMPORARY sensitive data access for the logged-in employee.
    Intended ONLY for self-verification.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        try:
            profile = user.employeeprofile
        except Exception:
            return Response(
                {"detail": "Employee profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = serializers.EmployeeSensitiveSelfSerializer(
            profile, context={"request": request})
        return Response({
            "temporary": True,
            "data": serializer.data
        })


class HREmployeeSensitiveDetailsAPIView(APIView):
    """
    PERMANENT sensitive data access for HR / Management.
    """
    permission_classes = [IsAuthenticated, IsHROrManagement]

    def get(self, request, emp_id):
        profile = get_object_or_404(EmployeeProfile, emp_id=emp_id)

        serializer = serializers.EmployeeSensitiveHRSerializer(
            profile, context={"request": request})
        return Response({
            "hr_access": True,
            "data": serializer.data
        })


class HRTLActionAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTLorHRorOwner]

    def post(self, request, leave_id):
        action = request.data.get("action", "").strip()
        remarks = request.data.get("remarks", "").strip()

        lr = get_object_or_404(models.LeaveRequest, id=leave_id)
        user = request.user

        if not action:
            return Response(
                {
                    "detail": "Action is required. Allowed values: approve or reject.",
                    "current_status": lr.status
                },
                status=400
            )

        if action not in ("approve", "reject"):
            return Response(
                {
                    "detail": "Invalid action. Allowed values: approve or reject.",
                    "current_status": lr.status
                },
                status=400
            )

        if user.role == "tl":

            if lr.profile.user == user:
                return Response(
                    {"detail": "TL cannot approve or reject their own leave."},
                    status=403
                )

            if lr.tl != user:
                return Response(
                    {"detail": "You are not authorized to act on this leave."},
                    status=403
                )

            if lr.tl is not None and lr.status != "tl_approved":
                return Response(
                    {
                        "detail": 'TL can only act on leave requests with status "applied".',
                        "current_status": lr.status
                    },
                    status=400
                )

            if action == "approve":
                lr.apply_tl_approval(user, approve=True, remarks=remarks)

                # Notify HR
                for hr_user in User.objects.filter(role__in=["hr", "management"]):
                    models.Notification.objects.create(
                        to_user=hr_user,
                        title=f"TL approved leave: {lr.profile.full_name()}",
                        body=f"Leave request {lr.id} is awaiting HR action.",
                        notif_type="leave",
                        extra={"leave_request_id": lr.id}
                    )

                return Response(
                    {
                        "detail": "Leave approved by TL.",
                        "status": "tl_approved"
                    },
                    status=200
                )

            if action == "reject":
                lr.apply_tl_approval(user, approve=False, remarks=remarks)

                models.Notification.objects.create(
                    to_user=lr.profile.user,
                    title="Leave rejected by TL",
                    body=remarks or "Your leave request was rejected by your Team Lead.",
                    notif_type="leave",
                    extra={"leave_request_id": lr.id}
                )

                return Response(
                    {
                        "detail": "Leave rejected by TL.",
                        "status": "tl_rejected"
                    },
                    status=200
                )

        if user.role in ("hr", "management"):

            # HR MUST WAIT FOR TL APPROVAL
            if lr.status != "tl_approved":
                return Response(
                    {
                        "detail": "HR cannot act until TL approves the leave.",
                        "current_status": lr.status
                    },
                    status=403
                )

            if action == "approve":
                try:
                    lr.apply_hr_approval(user, approve=True, remarks=remarks)
                except DjangoValidationError as e:
                    return Response(
                        {"detail": e.messages},
                        status=400
                    )

                return Response(
                    {
                        "detail": "Leave approved by HR.",
                        "status": "hr_approved"
                    },
                    status=200
                )

            if action == "reject":
                try:
                    lr.apply_hr_approval(user, approve=False, remarks=remarks)
                except DjangoValidationError as e:
                    return Response(
                        {"detail": e.messages},
                        status=400
                    )

                return Response(
                    {
                        "detail": "Leave rejected by HR.",
                        "status": "hr_rejected"
                    },
                    status=200
                )

        return Response(
            {"detail": "You are not allowed to perform this action."},
            status=403
        )


class TimesheetDailyFormAPIView(APIView):
    """
    GET -> returns today's date/day, optional clock_in/out (from TimesheetDay or entries),
    existing entries, and total hours for the day.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        prof = getattr(user, "employeeprofile", None)
        if not prof:
            return Response({"detail": "Employee profile not found."}, status=400)

        today = timezone.localdate()

        ts_day, _ = TimesheetDay.objects.get_or_create(
            profile=prof, date=today)

        entries_qs = TimesheetEntry.objects.filter(
            profile=prof,
            date=today
        ).order_by("start_time")

        entries_ser = TimesheetEntrySerializer(entries_qs, many=True).data

        attendance = Attendance.objects.filter(user=user, date=today).first()

        att_clock_in = attendance.clock_in if attendance else None
        att_clock_out = attendance.clock_out if attendance else None

        clock_in = att_clock_in or ts_day.clock_in or (
            entries_qs.first().start_time if entries_qs.exists() else None
        )
        clock_out = att_clock_out or ts_day.clock_out or (
            entries_qs.last().end_time if entries_qs.exists() else None
        )

        if attendance and attendance.duration_seconds:
            total_seconds = attendance.duration_seconds

        else:
            total_seconds = sum(e.duration_seconds or 0 for e in entries_qs)

        total_hours = round(total_seconds / 3600.0, 2)

        return Response({
            "date": today.isoformat(),
            "day": today.strftime("%A"),
            "clock_in": clock_in,
            "clock_out": clock_out,
            "existing_entries": entries_ser,
            "total_hours_workdone": total_hours,
        }, status=200)


class TimesheetDailyUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        prof = user.employeeprofile

        serializer = DailyTimesheetUpdateSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        date = serializer.validated_data["date"]
        entries = serializer.validated_data["entries"]

        attendance = Attendance.objects.filter(
            user=user,
            date=date
        ).first()

        if not attendance or not attendance.clock_in:
            return Response(
                {"detail": "Attendance clock-in not found for this date."},
                status=400
            )

        ts_day, created = TimesheetDay.objects.get_or_create(
            profile=prof,
            date=date
        )

        if ts_day.is_submitted:
            return Response(
                {"detail": "Timesheet already submitted."},
                status=400
            )

        ts_day.attendance = attendance

        TimesheetEntry.objects.filter(profile=prof, date=date).delete()

        saved = []
        for e in entries:
            start_dt = timezone.make_aware(
                datetime.combine(date, e["start_time"]),
                timezone.get_current_timezone()
            )

            end_dt = timezone.make_aware(
                datetime.combine(date, e["end_time"]),
                timezone.get_current_timezone()
            )

            saved.append(
                TimesheetEntry.objects.create(
                    profile=prof,
                    date=date,
                    day=date.strftime("%A"),
                    task=e["task"],
                    description=e.get("description", ""),
                    start_time=start_dt,
                    end_time=end_dt,
                )
            )

        # ✅ Attendance controls clock-in / clock-out — ALWAYS
        ts_day.clock_in = attendance.clock_in
        ts_day.clock_out = attendance.clock_out
        ts_day.last_modified_by = user
        ts_day.save(
            update_fields=[
                "attendance",
                "clock_in",
                "clock_out",
                "last_modified_by",
                "updated_at",
            ]
        )

        total_seconds = sum(o.duration_seconds or 0 for o in saved)
        entries_out = TimesheetEntrySerializer(saved, many=True).data

        return Response({
            "message": "Timesheet saved.",
            "date": date,
            "is_submitted": ts_day.is_submitted,
            "clock_in": timezone.localtime(attendance.clock_in) if attendance.clock_in else None,
            "clock_out": timezone.localtime(attendance.clock_out) if attendance.clock_out else None,
            "total_hours": round(total_seconds / 3600, 2),
            "entries": entries_out
        }, status=201)


class TimesheetSubmitAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        prof = user.employeeprofile
        date = request.data.get("date")

        if not date:
            return Response({"detail": "date is required"}, status=400)

        date = parse_date(date)
        ts_day = get_object_or_404(
            TimesheetDay,
            profile=prof,
            date=date
        )

        if ts_day.is_submitted:
            return Response({"detail": "Already submitted"}, status=400)

        if not TimesheetEntry.objects.filter(profile=prof, date=date).exists():
            return Response({"detail": "No entries to submit"}, status=400)

        ts_day.is_submitted = True
        ts_day.submitted_at = timezone.now()
        ts_day.last_modified_by = user
        ts_day.save()

        return Response({
            "message": "Timesheet submitted and locked",
            "date": date
        }, status=200)


class TimesheetDailyForHRAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTLorHRorOwner]

    def get(self, request):
        raw_emp_id = request.query_params.get("emp_id")
        raw_date = request.query_params.get("date")

        if not raw_emp_id or not raw_date:
            return Response({
                "detail": "emp_id and date are required (e.g. ?emp_id=WZG-AI-0006&date=2025-12-10)."
            }, status=status.HTTP_400_BAD_REQUEST)

        emp_id = unquote(str(raw_emp_id)).strip()
        date_str = unquote(str(raw_date)).strip()

        date_obj = parse_date(date_str)
        if not date_obj:
            dt = parse_datetime(date_str)
            if dt:
                date_obj = dt.date()
        if not date_obj:
            return Response({"detail": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        prof = get_object_or_404(EmployeeProfile, emp_id=emp_id)

        ts_day = TimesheetDay.objects.filter(
            profile=prof, date=date_obj).first()
        entries_qs = TimesheetEntry.objects.filter(
            profile=prof, date=date_obj).order_by("start_time")
        entries_ser = TimesheetEntrySerializer(entries_qs, many=True).data

        clock_in = ts_day.clock_in if ts_day and ts_day.clock_in else (
            entries_qs.first().start_time if entries_qs.exists() else None)
        clock_out = ts_day.clock_out if ts_day and ts_day.clock_out else (
            entries_qs.last().end_time if entries_qs.exists() else None)

        total_seconds = sum(
            (int(e.duration_seconds) if e.duration_seconds is not None else 0) for e in entries_qs)
        total_hours = round(total_seconds / 3600.0, 2)

        return Response({
            "ok": True,
            "employee": _employee_display_name(prof),
            "emp_id": prof.emp_id,
            "date": date_obj.isoformat(),
            "clock_in": clock_in,
            "clock_out": clock_out,
            "entries": entries_ser,
            "total_hours_workdone": total_hours
        }, status=status.HTTP_200_OK)


class TimesheetMonthlyForHRAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTLorHRorOwner]

    def get(self, request):
        raw_emp_id = request.query_params.get("emp_id")
        raw_month = request.query_params.get("month")

        if not raw_emp_id:
            return Response({"detail": "emp_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        emp_id = unquote(str(raw_emp_id)).strip()
        today = timezone.localdate()

        if raw_month:
            month_str = unquote(str(raw_month)).strip()
            try:
                year, month = map(int, month_str.split("-"))
            except Exception:
                return Response({"detail": "Invalid month format. Use YYYY-MM."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            year = today.year
            month = today.month

        if not (1 <= month <= 12):
            return Response({"detail": "Invalid month number (1..12)."}, status=status.HTTP_400_BAD_REQUEST)

        prof = get_object_or_404(EmployeeProfile, emp_id=emp_id)

        entries_qs = TimesheetEntry.objects.filter(
            profile=prof, date__year=year, date__month=month).order_by("date", "start_time")

        day_map = {}
        for entry in entries_qs:
            d = entry.date
            if d not in day_map:
                day_map[d] = {
                    "date": d.isoformat(),
                    "clock_in": entry.start_time,
                    "clock_out": entry.end_time,
                    "total_seconds": 0,
                }
            info = day_map[d]
            if entry.start_time < info["clock_in"]:
                info["clock_in"] = entry.start_time
            if entry.end_time > info["clock_out"]:
                info["clock_out"] = entry.end_time
            try:
                sec = int(
                    entry.duration_seconds) if entry.duration_seconds is not None else 0
            except (TypeError, ValueError):
                sec = 0
            info["total_seconds"] += sec

        days = []
        for d in sorted(day_map.keys()):
            info = day_map[d]
            days.append({
                "date": info["date"],
                "clock_in": info["clock_in"],
                "clock_out": info["clock_out"],
                "total_hours_workdone": round(info["total_seconds"] / 3600.0, 2),
            })

        month_total_seconds = sum(info["total_seconds"]
                                  for info in day_map.values())
        month_total_hours = round(month_total_seconds / 3600.0, 2)

        return Response({
            "employee": _employee_display_name(prof),
            "emp_id": prof.emp_id,
            "month": f"{year}-{month:02d}",
            "total_hours_workdone": month_total_hours,
            "days": days,
        }, status=status.HTTP_200_OK)


class TimesheetWorksheetForHRAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTLorHRorOwner]

    def get(self, request):
        raw_emp_id = request.query_params.get("emp_id")
        from_q = request.query_params.get("from")
        to_q = request.query_params.get("to")

        if not raw_emp_id:
            return Response({"detail": "emp_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        emp_id = unquote(str(raw_emp_id)).strip()

        try:
            d_from = parse_date(from_q) if from_q else None
            d_to = parse_date(to_q) if to_q else None
        except Exception:
            return Response({"detail": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        today = timezone.localdate()
        if not d_from and not d_to:
            d_from = today.replace(day=1)
            d_to = today
        elif d_from and not d_to:
            d_to = d_from
        elif d_to and not d_from:
            d_from = d_to

        if d_from > d_to:
            return Response({"detail": "'from' must be <= 'to'."}, status=status.HTTP_400_BAD_REQUEST)

        prof = get_object_or_404(EmployeeProfile, emp_id=emp_id)
        entries_qs = TimesheetEntry.objects.filter(
            profile=prof, date__gte=d_from, date__lte=d_to).order_by("date", "start_time")
        entries_ser = TimesheetEntrySerializer(entries_qs, many=True).data

        total_seconds = sum(
            (int(e.duration_seconds) if e.duration_seconds is not None else 0) for e in entries_qs)
        total_hours = round(total_seconds / 3600.0, 2)

        return Response({
            "employee": _employee_display_name(prof),
            "emp_id": prof.emp_id,
            "from": d_from.isoformat(),
            "to": d_to.isoformat(),
            "total_hours": total_hours,
            "entries": entries_ser
        }, status=status.HTTP_200_OK)


class TimesheetYearlyForHRAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTLorHRorOwner]

    def get(self, request):
        raw_emp_id = request.query_params.get("emp_id")
        raw_year = request.query_params.get("year")

        if not raw_emp_id or not raw_year:
            return Response({"detail": "emp_id and year are required (YYYY)."}, status=status.HTTP_400_BAD_REQUEST)

        emp_id = unquote(str(raw_emp_id)).strip()
        try:
            year = int(raw_year)
            if year < 1900 or year > 9999:
                raise ValueError()
        except Exception:
            return Response({"detail": "Invalid year. Use YYYY (e.g. 2025)."}, status=status.HTTP_400_BAD_REQUEST)

        prof = get_object_or_404(EmployeeProfile, emp_id=emp_id)
        entries_qs = TimesheetEntry.objects.filter(
            profile=prof, date__year=year).order_by("date", "start_time")

        from collections import defaultdict
        months_map = defaultdict(lambda: defaultdict(
            lambda: {"entries": [], "total_seconds": 0, "clock_in": None, "clock_out": None}))

        for e in entries_qs:
            m = e.date.month
            d = e.date.isoformat()
            info = months_map[m][d]
            info["entries"].append(TimesheetEntrySerializer(e).data)
            sec = int(e.duration_seconds) if e.duration_seconds is not None else 0
            info["total_seconds"] += sec
            if info["clock_in"] is None or e.start_time < info["clock_in"]:
                info["clock_in"] = e.start_time
            if info["clock_out"] is None or e.end_time > info["clock_out"]:
                info["clock_out"] = e.end_time

        months = []
        year_total_seconds = 0
        for month_num in range(1, 13):
            month_days = months_map.get(month_num, {})
            days_list = []
            month_total_seconds = 0
            for d_iso in sorted(month_days.keys()):
                info = month_days[d_iso]
                month_total_seconds += info["total_seconds"]
                days_list.append({
                    "date": d_iso,
                    "clock_in": info["clock_in"],
                    "clock_out": info["clock_out"],
                    "total_hours": round(info["total_seconds"] / 3600.0, 2),
                    "entries_count": len(info["entries"]),
                })
            months.append({
                "month": f"{timezone.datetime(year, month_num, 1).strftime('%Y-%m')}",
                "total_hours": round(month_total_seconds / 3600.0, 2),
                "days": days_list
            })
            year_total_seconds += month_total_seconds

        return Response({
            "employee": _employee_display_name(prof),
            "emp_id": prof.emp_id,
            "year": str(year),
            "year_total_hours": round(year_total_seconds / 3600.0, 2),
            "months": months
        }, status=status.HTTP_200_OK)


class TimesheetDailyForTLAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTLOnly]

    def get(self, request):
        raw_emp_id = request.query_params.get("emp_id")
        raw_date = request.query_params.get("date")
        if not raw_emp_id or not raw_date:
            return Response({"detail": "emp_id and date are required (YYYY-MM-DD)."}, status=400)

        emp_id = unquote(str(raw_emp_id)).strip()
        date_str = unquote(str(raw_date)).strip()

        date_obj = parse_date(date_str)
        if not date_obj:
            dt = parse_datetime(date_str)
            if dt:
                date_obj = dt.date()
        if not date_obj:
            return Response({"detail": "Invalid date format. Use YYYY-MM-DD."}, status=400)

        prof = get_object_or_404(EmployeeProfile, emp_id=emp_id)
        ts_day = TimesheetDay.objects.filter(
            profile=prof, date=date_obj).first()
        entries_qs = TimesheetEntry.objects.filter(
            profile=prof, date=date_obj).order_by("start_time")
        entries_ser = TimesheetEntrySerializer(entries_qs, many=True).data

        clock_in = ts_day.clock_in if ts_day and ts_day.clock_in else (
            entries_qs.first().start_time if entries_qs.exists() else None)
        clock_out = ts_day.clock_out if ts_day and ts_day.clock_out else (
            entries_qs.last().end_time if entries_qs.exists() else None)
        total_seconds = sum(
            (int(e.duration_seconds) if e.duration_seconds is not None else 0) for e in entries_qs)
        total_hours = round(total_seconds / 3600.0, 2)

        return Response({
            "ok": True,
            "employee": _employee_display_name(prof),
            "emp_id": prof.emp_id,
            "date": date_obj.isoformat(),
            "clock_in": clock_in,
            "clock_out": clock_out,
            "entries": entries_ser,
            "total_hours_workdone": total_hours
        }, status=200)


class TimesheetMonthlyForTLAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTLOnly]

    def get(self, request):
        raw_emp_id = request.query_params.get("emp_id")
        raw_month = request.query_params.get("month")

        if not raw_emp_id:
            return Response({"detail": "emp_id is required."}, status=400)

        emp_id = unquote(str(raw_emp_id)).strip()
        today = timezone.localdate()

        if raw_month:
            month_str = unquote(str(raw_month)).strip()
            try:
                year, month = map(int, month_str.split("-"))
            except Exception:
                return Response({"detail": "Invalid month format. Use YYYY-MM."}, status=400)
        else:
            year = today.year
            month = today.month

        if not (1 <= month <= 12):
            return Response({"detail": "Invalid month number (1..12)."}, status=400)

        prof = get_object_or_404(EmployeeProfile, emp_id=emp_id)
        entries_qs = TimesheetEntry.objects.filter(
            profile=prof, date__year=year, date__month=month).order_by("date", "start_time")

        day_map = {}
        for entry in entries_qs:
            d = entry.date
            if d not in day_map:
                day_map[d] = {"date": d.isoformat(
                ), "clock_in": entry.start_time, "clock_out": entry.end_time, "total_seconds": 0}
            info = day_map[d]
            if entry.start_time < info["clock_in"]:
                info["clock_in"] = entry.start_time
            if entry.end_time > info["clock_out"]:
                info["clock_out"] = entry.end_time
            sec = int(
                entry.duration_seconds) if entry.duration_seconds is not None else 0
            info["total_seconds"] += sec

        days = []
        for d in sorted(day_map.keys()):
            info = day_map[d]
            days.append({"date": info["date"], "clock_in": info["clock_in"], "clock_out": info["clock_out"],
                        "total_hours_workdone": round(info["total_seconds"] / 3600.0, 2)})

        month_total_seconds = sum(info["total_seconds"]
                                  for info in day_map.values())
        month_total_hours = round(month_total_seconds / 3600.0, 2)

        return Response({
            "employee": _employee_display_name(prof),
            "emp_id": prof.emp_id,
            "month": f"{year}-{month:02d}",
            "total_hours_workdone": month_total_hours,
            "days": days
        }, status=200)


class TimesheetWorksheetForTLAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTLOnly]

    def get(self, request):
        emp_id = request.query_params.get("emp_id")
        from_q = request.query_params.get("from")
        to_q = request.query_params.get("to")

        if not emp_id:
            return Response({"detail": "emp_id is required."}, status=400)

        try:
            d_from = parse_date(from_q) if from_q else None
            d_to = parse_date(to_q) if to_q else None
        except Exception:
            return Response({"detail": "Invalid date format. Use YYYY-MM-DD."}, status=400)

        today = timezone.localdate()
        if not d_from and not d_to:
            d_from = today.replace(day=1)
            d_to = today
        elif d_from and not d_to:
            d_to = d_from
        elif d_to and not d_from:
            d_from = d_to

        if d_from > d_to:
            return Response({"detail": "'from' must be <= 'to'."}, status=400)

        prof = get_object_or_404(EmployeeProfile, emp_id=emp_id)
        entries_qs = TimesheetEntry.objects.filter(
            profile=prof, date__gte=d_from, date__lte=d_to).order_by("date", "start_time")
        entries_ser = TimesheetEntrySerializer(entries_qs, many=True).data

        total_seconds = sum(
            (int(e.duration_seconds) if e.duration_seconds is not None else 0) for e in entries_qs)
        total_hours = round(total_seconds / 3600.0, 2)

        return Response({
            "employee": _employee_display_name(prof),
            "emp_id": prof.emp_id,
            "from": d_from.isoformat(),
            "to": d_to.isoformat(),
            "total_hours": total_hours,
            "entries": entries_ser
        }, status=200)


class TimesheetYearlyForTLAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTLOnly]

    def get(self, request):
        emp_id = request.query_params.get("emp_id")
        year_q = request.query_params.get("year")

        if not emp_id or not year_q:
            return Response({"detail": "emp_id and year are required (YYYY)."}, status=400)

        try:
            year = int(year_q)
            if year < 1900 or year > 9999:
                raise ValueError()
        except Exception:
            return Response({"detail": "Invalid year. Use YYYY (e.g. 2025)."}, status=400)

        prof = get_object_or_404(EmployeeProfile, emp_id=emp_id)
        entries_qs = TimesheetEntry.objects.filter(
            profile=prof, date__year=year).order_by("date", "start_time")

        from collections import defaultdict
        months_map = defaultdict(lambda: defaultdict(
            lambda: {"entries": [], "total_seconds": 0, "clock_in": None, "clock_out": None}))

        for e in entries_qs:
            m = e.date.month
            d = e.date.isoformat()
            info = months_map[m][d]
            info["entries"].append(TimesheetEntrySerializer(e).data)
            sec = int(e.duration_seconds) if e.duration_seconds is not None else 0
            info["total_seconds"] += sec
            if info["clock_in"] is None or e.start_time < info["clock_in"]:
                info["clock_in"] = e.start_time
            if info["clock_out"] is None or e.end_time > info["clock_out"]:
                info["clock_out"] = e.end_time

        months = []
        year_total_seconds = 0
        for month_num in range(1, 13):
            month_days = months_map.get(month_num, {})
            days_list = []
            month_total_seconds = 0
            for d_iso in sorted(month_days.keys()):
                info = month_days[d_iso]
                month_total_seconds += info["total_seconds"]
                days_list.append({
                    "date": d_iso,
                    "clock_in": info["clock_in"],
                    "clock_out": info["clock_out"],
                    "total_hours": round(info["total_seconds"] / 3600.0, 2),
                    "entries_count": len(info["entries"]),
                })
            months.append({
                "month": f"{timezone.datetime(year, month_num, 1).strftime('%Y-%m')}",
                "total_hours": round(month_total_seconds / 3600.0, 2),
                "days": days_list
            })
            year_total_seconds += month_total_seconds

        return Response({
            "employee": _employee_display_name(prof),
            "emp_id": prof.emp_id,
            "year": str(year),
            "year_total_hours": round(year_total_seconds / 3600.0, 2),
            "months": months
        }, status=200)


class PolicyListAPIView(generics.ListAPIView):
    queryset = models.Policy.objects.all().order_by('-created_at')
    serializer_class = serializers.PolicySerializer
    permission_classes = [IsAuthenticated]


class PolicyCreateAPIView(generics.CreateAPIView):
    queryset = models.Policy.objects.all()
    serializer_class = serializers.PolicySerializer
    permission_classes = [IsHROrManagement]

    def perform_create(self, serializer):
        policy = serializer.save()

        employees = User.objects.all()  # all employees
        for emp in employees:
            Notification.objects.create(
                to_user=emp,
                title=f"New Policy Added: {policy.title}",
                body=f"A new policy '{policy.title}' has been added.",
                notif_type='policy',
                is_read=False
            )


class PolicyRetrieveAPIView(generics.RetrieveAPIView):
    queryset = models.Policy.objects.all()
    serializer_class = serializers.PolicySerializer
    permission_classes = [IsAuthenticated]


class PolicyUpdateDeleteAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Policy.objects.all()
    serializer_class = serializers.PolicySerializer
    permission_classes = [IsHROrManagement]

    def perform_update(self, serializer):
        policy = serializer.save()

        employees = User.objects.all()
        for emp in employees:
            Notification.objects.create(
                to_user=emp,
                title=f"Policy Updated: {policy.title}",
                body=f"The policy '{policy.title}' has been updated.",
                notif_type='policy',
                is_read=False
            )

    def perform_destroy(self, instance):
        policy_title = instance.title
        instance.delete()

        employees = User.objects.all()
        for emp in employees:
            Notification.objects.create(
                to_user=emp,
                title=f"Policy Deleted: {policy_title}",
                body=f"The policy '{policy_title}' has been deleted.",
                notif_type='policy',
                is_read=False
            )


class HRDashboardStatsAPIView(APIView):
    permission_classes = [IsHROrManagement]

    def get(self, request):
        today = timezone.localdate()

        # 1. Total Active Employees
        total_employees = EmployeeProfile.objects.filter(
            is_active=True).count()

        # 2. Present Employees (Clocked in today)
        present_employees = Attendance.objects.filter(
            date=today
        ).exclude(status='absent').count()

        # 3. On Leave Employees (Approved leaves active today)
        on_leave_employees = models.LeaveRequest.objects.filter(
            start_date__lte=today,
            end_date__gte=today,
            status__in=['hr_approved', 'tl_approved']
        ).count()

        workforce_roles = ['employee', 'intern', 'tl']
        total_employees = User.objects.filter(
            role__in=workforce_roles, is_active=True).count()

        # Present Today
        present_today = Attendance.objects.filter(
            date=today,
            user__role__in=workforce_roles,
            status__in=['Working', 'Completed']
        ).values('user').distinct().count()

        # On Leave (Total - Present)
        on_leave = max(0, total_employees - present_today)

        return Response({
            "total_employees": total_employees,
            "present_employees": present_employees,
            "on_leave_employees": on_leave_employees
        })
