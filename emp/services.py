from django.utils import timezone
from django.db import transaction,IntegrityError
from emp.models import Attendance
from datetime import datetime,time
from django.db.models import Q
class AttendanceService:

    @staticmethod
    @transaction.atomic
    def clock_in(user):
        today=timezone.localdate()
        now=timezone.localtime()
        try:
            attendance=Attendance.objects.create(user=user,date=today,clock_in=timezone.now(),status='working')
            return attendance
        except IntegrityError:
            return None
    
    def clock_out(user):
        today = timezone.localdate()

        at = Attendance.objects.filter(
            user=user,
            date=today
        ).first()

        # No clock-in found
        if not at:
            return None, "NO_CLOCK_IN"

        # Already clocked out
        if at.clock_out:
            return None, "ALREADY_CLOCKED_OUT"

        # Perform clock-out
        at.clock_out = timezone.now()
        at.compute_duration_and_overtime()
        at.save()

        return at, None
class AttendanceReportService:
    """
    Handles attendance reporting business logic
    """

    REGULAR_WORK_SECONDS = 9 * 60 * 60       # 9 hours
    LATE_TIME_LIMIT = time(9, 45)            # 9:45 AM

    @staticmethod
    def get_attendance_queryset(user, month=None):
        if month:
            year, month_num = map(int, month.split("-"))
            return Attendance.objects.filter(
                user=user,
                date__year=year,
                date__month=month_num
            ).order_by("-date")

        return Attendance.objects.filter(user=user).order_by("-date")[:30]

    @staticmethod
    def calculate_monthly_summary(attendances):
        total_seconds = 0
        overtime_seconds = 0
        late_count = 0

        for attendance in attendances:
            worked_seconds = 0

            # Total worked hours
            if attendance.clock_in and attendance.clock_out and attendance.duration_time:
                worked_seconds = attendance.duration_time.total_seconds()
                total_seconds += worked_seconds

            # Overtime calculation
            if worked_seconds > AttendanceReportService.REGULAR_WORK_SECONDS:
                overtime_seconds += (
                    worked_seconds - AttendanceReportService.REGULAR_WORK_SECONDS
                )

            # Late arrival count
            if attendance.clock_in:
                clock_in_time = timezone.localtime(attendance.clock_in).time()
                if clock_in_time > AttendanceReportService.LATE_TIME_LIMIT:
                    late_count += 1

        return {
            "total_seconds": total_seconds,
            "overtime_seconds": overtime_seconds,
            "late_count": late_count,
        }

    @staticmethod
    def format_seconds(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours:02d}:{minutes:02d}"
class AttendanceQueryService:
    """
    Handles attendance query logic based on user roles
    """

    @staticmethod
    def get_today_attendance(user):
        today = timezone.localdate()

        queryset = Attendance.objects.filter(date=today)

        # Employee can see only their own attendance
        if user.role == "employee":
            queryset = queryset.filter(user=user)

        # TL and HR can see their own + employees attendance
        elif user.role in ["tl", "hr"]:
            queryset = queryset.filter(
                Q(user=user) | Q(user__role="employee")
            )

        else:
            return None

        return queryset.select_related("user").order_by("user__username")
                                                 