# emp/views.py
import json
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Sum, Count
import calendar
from .serializers import EmployeeCreateSerializer, EmployeeProfileReadSerializer
from . import models, serializers
from .permissions import IsHROrManagement, IsTLorHRorOwner
from django.contrib.auth import get_user_model
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Attendance

User = get_user_model()

# --- Profile ---


class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        prof = request.user.employeeprofile
        return Response(serializers.EmployeeProfileReadSerializer(prof).data)


class UpdateContactView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        prof = request.user.employeeprofile
        serializer = serializers.EmployeeContactUpdateSerializer(
            prof, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UpdateIdentificationView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        prof = request.user.employeeprofile
        serializer = serializers.EmployeeIdentificationSerializer(
            prof, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

# --- Notifications ---


class MyNotificationsList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.NotificationSerializer

    def get_queryset(self):
        q = models.Notification.objects.filter(to_user=self.request.user)
        if self.request.query_params.get('unread') in ('true', '1', 'True'):
            q = q.filter(is_read=False)
        return q


class MarkNotificationsRead(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ids = request.data.get('ids', [])
        models.Notification.objects.filter(
            id__in=ids, to_user=request.user).update(is_read=True)
        return Response({"marked": len(ids)})

# --- Dashboard ---


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
            total_seconds/3600, 2)}

        project_status = []  # placeholder for React; they will fetch separate API if exists

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

# --- Attendance ---


class ClockInAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        today = timezone.localdate()
        if models.Attendance.objects.filter(user=user, date=today).exists():
            return Response({"detail": "Attendance for today already exists."}, status=400)
        shift_id = request.data.get('shift')
        shift = None
        if shift_id:
            shift = get_object_or_404(models.Shift, id=shift_id)
        att = models.Attendance.objects.create(user=user, date=today, shift=shift, clock_in=timezone.now(
        ), status='in_progress', note=request.data.get('note', ''))
        return Response(serializers.AttendanceReadSerializer(att).data, status=201)


class ClockOutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        today = timezone.localdate()
        att = models.Attendance.objects.filter(user=user, date=today).first()
        if not att:
            return Response({"detail": "No clock-in found for today."}, status=400)
        if att.clock_out:
            return Response({"detail": "Already clocked out."}, status=400)
        att.clock_out = timezone.now()
        att.status = 'completed'
        att.compute_duration_and_overtime()
        att.save()
        return Response(serializers.AttendanceReadSerializer(att).data)


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

# --- Calendar ---


class CalendarEventsAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.CalendarEventSerializer

    def get_queryset(self):
        year = int(self.request.query_params.get(
            'year', timezone.localdate().year))
        month = int(self.request.query_params.get(
            'month', timezone.localdate().month))
        q = models.CalendarEvent.objects.filter(
            date__year=year, date__month=month)
        return q

# --- Payroll ---


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
        # TODO: implement PDF generation (ReportLab or WeasyPrint)
        return Response({'download_url': f'/media/payslips/{prof.emp_id}-{year}-{month}.pdf', 'payslip': serializers.PayslipSerializer(payslip).data})

# --- Leave ---


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

        # ------------------------------------------------------------------
        # 1. If the applicant is a TL → route to HR directly
        # ------------------------------------------------------------------
        if request.user.role == 'tl':
            route_direct_to_hr = True
            actionable_tl = None
        else:
            route_direct_to_hr = False
            actionable_tl = None

        # ------------------------------------------------------------------
        # 2. Employee case → Select actionable TL (if any)
        # ------------------------------------------------------------------
        if not route_direct_to_hr:
            primary_tl = getattr(prof, 'team_lead', None)
            if primary_tl and not getattr(primary_tl, 'is_active', True):
                primary_tl = None
            actionable_tl = primary_tl

            if not primary_tl:
                # no assigned TL -> route to HR
                route_direct_to_hr = True
            else:
                # TL exists -> check if TL is on leave
                tl_profile = getattr(primary_tl, 'employeeprofile', None)
                if tl_profile and tl_profile.is_on_leave(start, end):
                    # TL unavailable -> find backup TL from same department
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

        # ------------------------------------------------------------------
        # 3. Auto-calculate leave duration
        # ------------------------------------------------------------------
        duration_days = ser.validated_data.get('calculated_days')
        if duration_days is None:
            duration_days = (end - start).days + 1

        # ------------------------------------------------------------------
        # 4. Create LeaveRequest with correct routing
        # ------------------------------------------------------------------
        if route_direct_to_hr:
            tl_user = None
            initial_status = 'pending_hr'   # <-- NEW: explicitly pending HR
        else:
            tl_user = actionable_tl
            initial_status = 'applied'

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

        # ------------------------------------------------------------------
        # 5. Notify actionable TL OR notify HR if pending_hr
        # ------------------------------------------------------------------
        if not route_direct_to_hr and actionable_tl:
            models.Notification.objects.create(
                to_user=actionable_tl,
                title=f"Leave request from {prof.full_name()}",
                body=f"{prof.full_name()} applied for {lr.leave_type} "
                f"from {lr.start_date} to {lr.end_date}.",
                notif_type='leave',
                extra={'leave_request_id': lr.id}
            )
        else:
            # pending HR: notify all HR and management users
            hr_users = User.objects.filter(
                role__in=['hr', 'management'], is_active=True)
            for hr_user in hr_users:
                models.Notification.objects.create(
                    to_user=hr_user,
                    title=f"Leave request pending HR: {prof.full_name()}",
                    body=f"{prof.full_name()} applied for {lr.leave_type} "
                    f"from {lr.start_date} to {lr.end_date}. Please review.",
                    notif_type='leave',
                    extra={'leave_request_id': lr.id}
                )

        # ------------------------------------------------------------------
        # 6. Response
        # ------------------------------------------------------------------
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


# --- HR support endpoints ---


class HRCreateEmployeeAPIView(APIView):
    permission_classes = [IsAuthenticated, IsHROrManagement]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        data = {}

        for key, value in request.data.items():
            if key in ["contact", "job", "bank", "identification"]:
                # Parse JSON string safely
                try:
                    data[key] = json.loads(value) if isinstance(
                        value, str) else value
                except Exception:
                    data[key] = value
            else:
                data[key] = value

        for key, file_obj in request.FILES.items():

            # contact.profile_photo
            if key.startswith("contact."):
                field = key.split("contact.")[1]
                if "contact" not in data or not isinstance(data["contact"], dict):
                    data["contact"] = {}
                data["contact"][field] = file_obj

            # job.id_image
            elif key.startswith("job."):
                field = key.split("job.")[1]
                if "job" not in data or not isinstance(data["job"], dict):
                    data["job"] = {}
                data["job"][field] = file_obj

            # identification.aadhaar_image, pan_image, passport_image
            elif key.startswith("identification."):
                field = key.split("identification.")[1]
                if "identification" not in data or not isinstance(data["identification"], dict):
                    data["identification"] = {}
                data["identification"][field] = file_obj

            # fallback (not expected)
            else:
                data[key] = file_obj

        serializer = EmployeeCreateSerializer(
            data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user, profile = serializer.save()
        return Response(EmployeeProfileReadSerializer(profile).data, status=status.HTTP_201_CREATED)


class HRTLActionAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTLorHRorOwner]

    def post(self, request, leave_id):
        action = request.data.get('action')  # 'approve' or 'reject'
        remarks = request.data.get('remarks', '')
        lr = get_object_or_404(models.LeaveRequest, id=leave_id)
        user = request.user

        # TL actions
        if user.role == 'tl':
            # TL cannot act on their own request
            if lr.profile.user == user:
                return Response({'detail': 'TL cannot approve their own leave.'}, status=403)
            # TL can act only on fresh applied requests
            if lr.status != 'applied':
                return Response({'detail': 'TL can only act on requests with status "applied".'}, status=400)

            if lr.profile.team_lead != user:
                return Response({'detail': 'Forbidden'}, status=403)

            if action == 'approve':
                lr.apply_tl_approval(user, approve=True, remarks=remarks)
                # notify HR users to review (only HR/management roles)
                for hr_user in User.objects.filter(role__in=['hr', 'management']):
                    models.Notification.objects.create(
                        to_user=hr_user,
                        title=f"TL approved leave: {lr.profile.full_name()}",
                        body=f"Leave {lr.id} ({lr.leave_type}) needs HR action.",
                        notif_type='leave',
                        extra={'leave_request_id': lr.id}
                    )
                return Response({'detail': 'tl_approved'})
            else:
                lr.apply_tl_approval(user, approve=False, remarks=remarks)
                models.Notification.objects.create(
                    to_user=lr.profile.user,
                    title='Leave rejected by TL',
                    body=remarks or 'Your leave was rejected by TL',
                    notif_type='leave',
                    extra={'leave_request_id': lr.id}
                )
                return Response({'detail': 'tl_rejected'})

        # HR actions
        if getattr(user, 'role', None) in ('hr', 'management'):
            # HR should act on requests that have TL approved OR pending HR
            if lr.status not in ('tl_approved', 'pending_hr'):
                return Response({'detail': 'HR can only act on requests that are approved by TL or routed to HR.'}, status=400)

            if action == 'approve':
                lr.apply_hr_approval(user, approve=True, remarks=remarks)
                # deduct balance if exists
                try:
                    lb = models.LeaveBalance.objects.get(
                        profile=lr.profile, leave_type__name=lr.leave_type)
                    lb.used = lb.used + lr.days
                    lb.save()
                except Exception:
                    # ignore if no matching balance
                    pass

                models.Notification.objects.create(
                    to_user=lr.profile.user,
                    title='Leave approved',
                    body=remarks or 'Your leave has been approved',
                    notif_type='leave',
                    extra={'leave_request_id': lr.id}
                )
                return Response({'detail': 'hr_approved'})
            else:
                lr.apply_hr_approval(user, approve=False, remarks=remarks)
                models.Notification.objects.create(
                    to_user=lr.profile.user,
                    title='Leave rejected by HR',
                    body=remarks or 'Your leave was rejected by HR',
                    notif_type='leave',
                    extra={'leave_request_id': lr.id}
                )
                return Response({'detail': 'hr_rejected'})

        return Response({'detail': 'Not allowed'}, status=403)











from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
from django.utils.dateparse import parse_datetime

from .models import TimesheetEntry, TimesheetDay, EmployeeProfile
from .serializers import (
    TimesheetEntrySerializer,
    TimesheetDaySerializer,
    DailyTimesheetUpdateSerializer,
)


# ============================================
# 1) GET: Daily form (today's data / summary)
# ============================================
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

        # Ensure there is a TimesheetDay row for today
        ts_day, _ = TimesheetDay.objects.get_or_create(profile=prof, date=today)

        # All entries for today
        entries_qs = TimesheetEntry.objects.filter(
            profile=prof,
            date=today
        ).order_by("start_time")

        # Serialize entries (this will show duration_seconds as HH:MM:SS)
        entries_ser = TimesheetEntrySerializer(entries_qs, many=True).data

        # Derive clock_in/out
        clock_in = ts_day.clock_in or (
            entries_qs.first().start_time if entries_qs.exists() else None
        )
        clock_out = ts_day.clock_out or (
            entries_qs.last().end_time if entries_qs.exists() else None
        )

        # Use model field duration_seconds (int) for totals
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


# =======================================================
# 2) POST: update today's entries (rules in serializer)
# =======================================================
class TimesheetDailyUpdateAPIView(APIView):
    """
    POST -> create / replace today's entries for the logged-in employee.

    All business rules are enforced in DailyTimesheetUpdateSerializer.validate():
      - employee must have Attendance clock_in for today
      - entries must be for today's date
      - entries cannot start before Attendance.clock_in
      - if Attendance.clock_out exists: entries cannot go beyond clock_out
      - if Attendance.clock_out does NOT exist: entries cannot go beyond now
      - max 6 hours per entry
      - entries cannot overlap
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        prof = getattr(user, "employeeprofile", None)
        if not prof:
            return Response({"detail": "Employee profile not found."}, status=400)

        today = timezone.localdate()

        # Serializer enforces attendance rules & entry validations
        ser = DailyTimesheetUpdateSerializer(
            data=request.data,
            context={"request": request}
        )
        ser.is_valid(raise_exception=True)
        payload = ser.validated_data
        entries_data = payload["entries"]

        # Get or create TimesheetDay (useful for reports / weekly summaries)
        ts_day, _ = TimesheetDay.objects.get_or_create(profile=prof, date=today)

        # Replace existing entries for the day
        TimesheetEntry.objects.filter(profile=prof, date=today).delete()
        saved_objs = []
        for item in entries_data:
            obj = TimesheetEntry.objects.create(
                profile=prof,
                date=today,
                day=today.strftime("%A"),
                task=item["task"],
                description=item.get("description", ""),
                start_time=item["start_time"],
                end_time=item["end_time"],
            )
            saved_objs.append(obj)

        # Optionally, set TimesheetDay clock_in/out from min/max entry times (for reporting)
        if saved_objs:
            ts_day.clock_in = min(o.start_time for o in saved_objs)
            ts_day.clock_out = max(o.end_time for o in saved_objs)
            ts_day.save()

        total_seconds = sum(o.duration_seconds or 0 for o in saved_objs)
        total_hours = round(total_seconds / 3600.0, 2)

        entries_out = TimesheetEntrySerializer(saved_objs, many=True).data

        return Response({
            "message": "Timesheet updated successfully",
            "date": today.isoformat(),
            "entries": entries_out,
            "total_hours_workdone": total_hours,
        }, status=201)

    
# Replace existing TimesheetDailyForHRAPIView with this version
# ---------- HR views: emp/views.py (paste below your existing imports/views) ----------
from urllib.parse import unquote
from django.utils.dateparse import parse_date, parse_datetime
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import TimesheetEntry, TimesheetDay, EmployeeProfile
from .serializers import TimesheetEntrySerializer, TimesheetDaySerializer
from .permissions import IsTLorHRorOwner


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


# ---------------------------
# HR: Daily view
# GET /api/timesheet/hr/daily/?emp_id=...&date=YYYY-MM-DD
# ---------------------------
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

        ts_day = TimesheetDay.objects.filter(profile=prof, date=date_obj).first()
        entries_qs = TimesheetEntry.objects.filter(profile=prof, date=date_obj).order_by("start_time")
        entries_ser = TimesheetEntrySerializer(entries_qs, many=True).data

        clock_in = ts_day.clock_in if ts_day and ts_day.clock_in else (entries_qs.first().start_time if entries_qs.exists() else None)
        clock_out = ts_day.clock_out if ts_day and ts_day.clock_out else (entries_qs.last().end_time if entries_qs.exists() else None)

        total_seconds = sum((int(e.duration_seconds) if e.duration_seconds is not None else 0) for e in entries_qs)
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


# ---------------------------
# HR: Monthly summary
# GET /api/timesheet/hr/monthly/?emp_id=...&month=YYYY-MM
# ---------------------------
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

        entries_qs = TimesheetEntry.objects.filter(profile=prof, date__year=year, date__month=month).order_by("date", "start_time")

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
                sec = int(entry.duration_seconds) if entry.duration_seconds is not None else 0
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

        month_total_seconds = sum(info["total_seconds"] for info in day_map.values())
        month_total_hours = round(month_total_seconds / 3600.0, 2)

        return Response({
            "employee": _employee_display_name(prof),
            "emp_id": prof.emp_id,
            "month": f"{year}-{month:02d}",
            "total_hours_workdone": month_total_hours,
            "days": days,
        }, status=status.HTTP_200_OK)


# ---------------------------
# HR: Worksheet (entries with IDs) for a date range
# GET /api/timesheet/hr/worksheet/?emp_id=...&from=YYYY-MM-DD&to=YYYY-MM-DD
# ---------------------------
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
        entries_qs = TimesheetEntry.objects.filter(profile=prof, date__gte=d_from, date__lte=d_to).order_by("date", "start_time")
        entries_ser = TimesheetEntrySerializer(entries_qs, many=True).data

        total_seconds = sum((int(e.duration_seconds) if e.duration_seconds is not None else 0) for e in entries_qs)
        total_hours = round(total_seconds / 3600.0, 2)

        return Response({
            "employee": _employee_display_name(prof),
            "emp_id": prof.emp_id,
            "from": d_from.isoformat(),
            "to": d_to.isoformat(),
            "total_hours": total_hours,
            "entries": entries_ser
        }, status=status.HTTP_200_OK)


# ---------------------------
# HR: Yearly summary (12 months)
# GET /api/timesheet/hr/yearly/?emp_id=...&year=YYYY
# ---------------------------
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
        entries_qs = TimesheetEntry.objects.filter(profile=prof, date__year=year).order_by("date", "start_time")

        from collections import defaultdict
        months_map = defaultdict(lambda: defaultdict(lambda: {"entries": [], "total_seconds": 0, "clock_in": None, "clock_out": None}))

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


# at top of emp/views.py add imports if missing
from urllib.parse import unquote
from django.utils.dateparse import parse_date, parse_datetime
from django.shortcuts import get_object_or_404
from rest_framework import status

# import permission
from .permissions import IsTLOnly

# ---------- helper for employee display name (reuse same helper) ----------
def _employee_display_name(prof):
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


# ---------- TL: daily view (same as HR daily) ----------
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
        ts_day = TimesheetDay.objects.filter(profile=prof, date=date_obj).first()
        entries_qs = TimesheetEntry.objects.filter(profile=prof, date=date_obj).order_by("start_time")
        entries_ser = TimesheetEntrySerializer(entries_qs, many=True).data

        clock_in = ts_day.clock_in if ts_day and ts_day.clock_in else (entries_qs.first().start_time if entries_qs.exists() else None)
        clock_out = ts_day.clock_out if ts_day and ts_day.clock_out else (entries_qs.last().end_time if entries_qs.exists() else None)
        total_seconds = sum((int(e.duration_seconds) if e.duration_seconds is not None else 0) for e in entries_qs)
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


# ---------- TL: monthly view ----------
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
        entries_qs = TimesheetEntry.objects.filter(profile=prof, date__year=year, date__month=month).order_by("date", "start_time")

        day_map = {}
        for entry in entries_qs:
            d = entry.date
            if d not in day_map:
                day_map[d] = {"date": d.isoformat(), "clock_in": entry.start_time, "clock_out": entry.end_time, "total_seconds": 0}
            info = day_map[d]
            if entry.start_time < info["clock_in"]:
                info["clock_in"] = entry.start_time
            if entry.end_time > info["clock_out"]:
                info["clock_out"] = entry.end_time
            sec = int(entry.duration_seconds) if entry.duration_seconds is not None else 0
            info["total_seconds"] += sec

        days = []
        for d in sorted(day_map.keys()):
            info = day_map[d]
            days.append({"date": info["date"], "clock_in": info["clock_in"], "clock_out": info["clock_out"], "total_hours_workdone": round(info["total_seconds"] / 3600.0, 2)})

        month_total_seconds = sum(info["total_seconds"] for info in day_map.values())
        month_total_hours = round(month_total_seconds / 3600.0, 2)

        return Response({
            "employee": _employee_display_name(prof),
            "emp_id": prof.emp_id,
            "month": f"{year}-{month:02d}",
            "total_hours_workdone": month_total_hours,
            "days": days
        }, status=200)


# ---------- TL: worksheet (entries with id) ----------
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
        entries_qs = TimesheetEntry.objects.filter(profile=prof, date__gte=d_from, date__lte=d_to).order_by("date", "start_time")
        entries_ser = TimesheetEntrySerializer(entries_qs, many=True).data

        total_seconds = sum((int(e.duration_seconds) if e.duration_seconds is not None else 0) for e in entries_qs)
        total_hours = round(total_seconds / 3600.0, 2)

        return Response({
            "employee": _employee_display_name(prof),
            "emp_id": prof.emp_id,
            "from": d_from.isoformat(),
            "to": d_to.isoformat(),
            "total_hours": total_hours,
            "entries": entries_ser
        }, status=200)


# ---------- TL: yearly summary ----------
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
        entries_qs = TimesheetEntry.objects.filter(profile=prof, date__year=year).order_by("date", "start_time")

        from collections import defaultdict
        months_map = defaultdict(lambda: defaultdict(lambda: {"entries": [], "total_seconds": 0, "clock_in": None, "clock_out": None}))

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
