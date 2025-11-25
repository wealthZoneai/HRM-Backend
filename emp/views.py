from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import EmployeeProfile, Attendance
from .serializers import (
    EmployeeReadSerializer,
    EmployeeCreateByHRSerializer,
    EmployeeUpdateByEmployeeSerializer,
    AttendanceReadSerializer,
    ClockInSerializer,
    ClockOutSerializer,
)
from .permissions import IsHRorManagement, IsOwnerOrHRorManagement
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import IntegrityError, transaction, models
from datetime import date
from django.db.models import Sum

# Create employee (HR/Management only)


class EmployeeCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsHRorManagement]

    def post(self, request):
        serializer = EmployeeCreateByHRSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return Response(EmployeeReadSerializer(profile).data, status=201)


# List employees (HR/Management only) - paginated, with simple search by name/emp_id
class EmployeeListAPIView(generics.ListAPIView):
    queryset = EmployeeProfile.objects.select_related('user').all()
    serializer_class = EmployeeReadSerializer
    permission_classes = [IsAuthenticated, IsHRorManagement]
    filter_backends = [filters.SearchFilter]
    search_fields = ['first_name', 'last_name', 'emp_id', 'department']

    # optional: override get_queryset to scope by management rules if needed
    # def get_queryset(self):
    #     qs = super().get_queryset()
    #     # apply extra filters if required
    #     return qs


# Retrieve / Partial update for profile
class EmployeeRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset = EmployeeProfile.objects.select_related('user').all()
    permission_classes = [IsAuthenticated, IsOwnerOrHRorManagement]
    lookup_field = 'pk'

    def get_serializer_class(self):
        # GET -> Read
        if self.request.method == 'GET':
            return EmployeeReadSerializer

        # PATCH/PUT -> choose by role
        user = self.request.user
        if getattr(user, 'role', None) in ('hr', 'management'):
            return EmployeeCreateByHRSerializer  # HR can update HR fields
        return EmployeeUpdateByEmployeeSerializer  # regular employee update

    def perform_update(self, serializer):
        profile = serializer.save()
        # ensure profile.role sync with user (already handled inside serializer.update)
        user = profile.user
        if hasattr(user, 'role') and profile.role and profile.role != user.role:
            user.role = profile.role
            user.save()


class MyProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = EmployeeProfile.objects.get(user=request.user)
        except EmployeeProfile.DoesNotExist:
            return Response(
                {"detail": "Employee profile does not exist for this user."},
                status=404
            )

        serializer = EmployeeReadSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        try:
            profile = EmployeeProfile.objects.get(user=request.user)
        except EmployeeProfile.DoesNotExist:
            return Response(
                {"detail": "Employee profile does not exist for this user."},
                status=404
            )

        serializer = EmployeeUpdateByEmployeeSerializer(
            profile, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# Helper: get user's attendance for today (or None)
def _get_today_attendance(user):
    today_local = timezone.localdate()
    return Attendance.objects.filter(user=user, date=today_local).first()


class ClockInAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ClockInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        now = timezone.now()
        today_local = timezone.localdate()

        # If existing row for today exists, disallow another clock-in:
        att = Attendance.objects.filter(user=user, date=today_local).first()
        if att:
            if att.status == 'in_progress' and att.clock_out is None:
                return Response({"detail": "Already clocked in. Please clock out before clocking in again."},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                # There is already a completed attendance for today — only allow one per day
                return Response({"detail": "Attendance for today already recorded."},
                                status=status.HTTP_400_BAD_REQUEST)

        # Create attendance row atomically, guarding unique_together integrity error
        try:
            with transaction.atomic():
                attendance = Attendance.objects.create(
                    user=user,
                    date=today_local,
                    clock_in=now,
                    status='in_progress',
                    note=serializer.validated_data.get('note', '')
                )
        except IntegrityError:
            return Response({"detail": "Attendance for today already exists (race condition)."},
                            status=status.HTTP_409_CONFLICT)

        data = AttendanceReadSerializer(attendance).data
        return Response(data, status=status.HTTP_201_CREATED)


class ClockOutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ClockOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        now = timezone.now()

        # Find open attendance for today
        att = _get_today_attendance(user)
        if not att:
            return Response({"detail": "No clock-in found for today."}, status=status.HTTP_400_BAD_REQUEST)
        if att.status != 'in_progress' or att.clock_out is not None:
            return Response({"detail": "Attendance already closed for today."}, status=status.HTTP_400_BAD_REQUEST)

        # Update clock_out and duration
        att.clock_out = now
        delta = att.clock_out - att.clock_in
        att.duration_seconds = int(delta.total_seconds())
        att.status = 'completed'
        att.note = att.note or serializer.validated_data.get('note', '')
        att.save()
        return Response(AttendanceReadSerializer(att).data, status=status.HTTP_200_OK)


# Monthly summary for the currently authenticated user
class MyAttendanceMonthlyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Query params:
          - month (YYYY-MM) optional, default = current month
        Returns list of days with attendance and aggregates.
        """
        user = request.user
        month = request.query_params.get('month')  # format 'YYYY-MM'
        if month:
            try:
                year, mon = month.split('-')
                year = int(year)
                mon = int(mon)
            except Exception:
                return Response({"detail": "month param must be YYYY-MM"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            today = timezone.localdate()
            year = today.year
            mon = today.month

        # Get all attendances for that month
        qs = Attendance.objects.filter(
            user=user, date__year=year, date__month=mon).order_by('date')

        serializer = AttendanceReadSerializer(qs, many=True)
        total_days_present = qs.count()
        total_seconds = qs.aggregate(total=Sum('duration_seconds'))[
            'total'] or 0
        avg_seconds_per_day = int(
            total_seconds / total_days_present) if total_days_present else 0

        response = {
            "year": year,
            "month": mon,
            "total_days_present": total_days_present,
            "total_hours_present": round(total_seconds / 3600, 2),
            "avg_hours_per_day": round(avg_seconds_per_day / 3600, 2),
            "attendances": serializer.data
        }
        return Response(response, status=status.HTTP_200_OK)


# Today status for dashboard (quick widget)
class MyAttendanceTodayStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        att = _get_today_attendance(user)
        if not att:
            return Response({"status": "not_clocked_in"}, status=status.HTTP_200_OK)
        if att.status == 'in_progress':
            return Response({
                "status": "clocked_in",
                "clock_in": att.clock_in,
                "attendance_id": att.id
            }, status=status.HTTP_200_OK)
        return Response({
            "status": "completed",
            "clock_in": att.clock_in,
            "clock_out": att.clock_out,
            "duration_seconds": att.duration_seconds
        }, status=status.HTTP_200_OK)


# HR/Management: attendance for a specific employee (monthly)
class HREmployeeAttendanceAPIView(APIView):
    permission_classes = [IsAuthenticated, IsHRorManagement]

    def get(self, request, user_id):
        month = request.query_params.get('month')
        if month:
            try:
                year, mon = month.split('-')
                year = int(year)
                mon = int(mon)
            except Exception:
                return Response({"detail": "month param must be YYYY-MM"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            today = timezone.localdate()
            year = today.year
            mon = today.month

        qs = Attendance.objects.filter(
            user__id=user_id, date__year=year, date__month=mon).order_by('date')
        serializer = AttendanceReadSerializer(qs, many=True)
        total_days_present = qs.count()
        total_seconds = qs.aggregate(total=Sum('duration_seconds'))[
            'total'] or 0
        response = {
            "user_id": user_id,
            "year": year,
            "month": mon,
            "total_days_present": total_days_present,
            "total_hours_present": round(total_seconds / 3600, 2),
            "attendances": serializer.data
        }
        return Response(response, status=status.HTTP_200_OK)


# HR/Management: aggregated report for all employees for a month (summary)
class HRMonthlyReportAPIView(APIView):
    permission_classes = [IsAuthenticated, IsHRorManagement]

    def get(self, request):
        month = request.query_params.get('month')
        if month:
            try:
                year, mon = month.split('-')
                year = int(year)
                mon = int(mon)
            except Exception:
                return Response({"detail": "month param must be YYYY-MM"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            today = timezone.localdate()
            year = today.year
            mon = today.month

        qs = Attendance.objects.filter(date__year=year, date__month=mon)
        # group by user: use values + annotate
        report = qs.values('user__id', 'user__username', 'user__first_name', 'user__last_name').annotate(
            days_present=models.Count('id'),
            total_seconds=models.Sum('duration_seconds')
        ).order_by('-days_present')

        data = []
        for r in report:
            total_seconds = r['total_seconds'] or 0
            data.append({
                "user_id": r['user__id'],
                "username": r['user__username'],
                "first_name": r['user__first_name'],
                "last_name": r['user__last_name'],
                "days_present": r['days_present'],
                "total_hours": round(total_seconds / 3600, 2)
            })

        return Response({
            "year": year,
            "month": mon,
            "report": data
        }, status=status.HTTP_200_OK)
