# hr/views.py
from tl.models import TLAnnouncement
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from emp.models import EmployeeProfile, Shift, Attendance, CalendarEvent, SalaryStructure, EmployeeSalary, Payslip, LeaveRequest, LeaveBalance, Notification
from . import serializers
from .permissions import IsHR, IsTL
from django.db.models import Sum, Count
from django.utils import timezone
import calendar
from django.contrib.auth import get_user_model
from . import models
from .serializers import AnnouncementSerializer, TLAnnouncementSerializer, MySalaryDetailSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Announcement
from django.db import IntegrityError
from django.utils.dateparse import parse_datetime


User = get_user_model()


class HRUpdateEmployeeContactAPIView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.EmployeeHRContactUpdateSerializer
    queryset = EmployeeProfile.objects.all()
    lookup_field = "pk"


class HRUpdateEmployeeRoleAPIView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.EmployeeHRRoleUpdateSerializer
    queryset = EmployeeProfile.objects.all()
    lookup_field = "pk"


class HRListEmployeesAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.EmployeeListSerializer
    queryset = EmployeeProfile.objects.all().select_related('user')


class HRRetrieveEmployeeAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.EmployeeDetailSerializer
    queryset = EmployeeProfile.objects.all()


class HRUpdateJobBankAPIView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.EmployeeJobBankUpdateSerializer
    queryset = EmployeeProfile.objects.all()
    lookup_field = 'pk'


class HRAttendanceListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.AttendanceAdminSerializer

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        month = self.request.query_params.get('month')
        department = self.request.query_params.get('department')
        qs = Attendance.objects.all().select_related(
            'user',
            'user__employeeprofile'
        )
        if user_id:
            qs = qs.filter(user__id=user_id)

        if department:
            qs = qs.filter(
                user__employeeprofile__department__iexact=department
            )

        if month:
            try:
                y, m = map(int, month.split('-'))
                qs = qs.filter(date__year=y, date__month=m)
            except (ValueError, AttributeError):
                pass

        return qs.order_by('-date')


class HRAttendanceRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    queryset = Attendance.objects.all()
    serializer_class = serializers.AttendanceAdminSerializer


class HRAttendanceCorrectAPIView(APIView):
    permission_classes = [IsAuthenticated, IsHR]

    def post(self, request, attendance_id):
        att = get_object_or_404(Attendance, id=attendance_id)

        clock_in_str = request.data.get("clock_in")
        clock_out_str = request.data.get("clock_out")
        note = request.data.get("note", "Corrected by HR")
        status = request.data.get("status")

        # Parse datetime safely
        if clock_in_str:
            clock_in = parse_datetime(clock_in_str)
            if clock_in:
                new_date = clock_in.date()

                # 🔒 Check UNIQUE constraint before changing date
                exists = Attendance.objects.filter(
                    user=att.user,
                    date=new_date
                ).exclude(id=att.id).exists()

                if not exists:
                    att.date = new_date  # ✅ safe to update
                # else: do NOT update date

                att.clock_in = clock_in

        if clock_out_str:
            clock_out = parse_datetime(clock_out_str)
            if clock_out:
                att.clock_out = clock_out

        if status:
            att.status = status
        new_note = f"HR correction: {note}"

        if not att.note:
            att.note = new_note
        elif new_note not in att.note:
            att.note += f"\n{new_note}"

        att.manual_entry = True
        att.save()

        return Response(serializers.AttendanceAdminSerializer(att).data)


class ShiftListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.ShiftSerializer
    queryset = Shift.objects.all()


class ShiftRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.ShiftSerializer
    queryset = Shift.objects.all()


class HRCalendarCreateAPIView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.CalendarEventSerializer
    queryset = CalendarEvent.objects.all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class HRCalendarUpdateAPIView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.CalendarEventSerializer
    queryset = CalendarEvent.objects.all()


class HRCalendarDeleteAPIView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    queryset = CalendarEvent.objects.all()


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def list_announcements(request):
    announcements = Announcement.objects.all().order_by("-date")
    serializer = AnnouncementSerializer(announcements, many=True)
    return Response({
        "success": True,
        "data": serializer.data
    })


@api_view(['PUT', 'PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsHR])
def update_announcement(request, pk):
    try:
        announce = Announcement.objects.get(pk=pk)
    except Announcement.DoesNotExist:
        return Response({"error": "Announcement not found"}, status=404)

    serializer = AnnouncementSerializer(
        announce, data=request.data, partial=True)
    if serializer.is_valid():
        announcement = serializer.save()

        employees = User.objects.filter(role__iexact="employee")
        employees = User.objects.filter(employeeprofile__isnull=False)

        for emp in employees:
            Notification.objects.create(
                to_user=emp,
                title="Announcement Updated",
                body=f"The announcement '{announcement.title}' was updated.",
                notif_type="announcement",
                extra={"announcement_id": announcement.id}
            )

        return Response({"success": True, "data": serializer.data})


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsHR])
def delete_announcement(request, pk):
    try:
        announce = Announcement.objects.get(pk=pk)
    except Announcement.DoesNotExist:
        return Response({"error": "Announcement not found"}, status=404)

    title = announce.title
    announce.delete()

    employees = User.objects.filter(role__iexact="employee")
    employees = User.objects.filter(employeeprofile__isnull=False)

    for emp in employees:
        Notification.objects.create(
            to_user=emp,
            title="Announcement Deleted",
            body=f"The announcement '{title}' was deleted.",
            notif_type="announcement"
        )

    return Response({"success": True, "message": "Deleted successfully"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def emp_tl_announcements(request):
    profile = EmployeeProfile.objects.filter(
        user=request.user).select_related('team_lead').first()
    if not profile:
        return Response({"message": "No profile found for user"}, status=404)

    tl = profile.team_lead
    if not tl:
        return Response({"message": "No Team Lead assigned"}, status=200)

    announcements = TLAnnouncement.objects.filter(created_by=tl)
    serializer = TLAnnouncementSerializer(announcements, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsHR])
def create_announcement(request):
    serializer = AnnouncementSerializer(data=request.data)
    if serializer.is_valid():
        announcement = serializer.save(created_by=request.user)

        if announcement.show_in_calendar:
            CalendarEvent.objects.create(
                title=announcement.title,
                description=announcement.description,
                event_type="announcement",
                date=announcement.date,
                start_time=announcement.time,
                created_by=request.user,
                extra={
                    "announcement_id": announcement.id,
                    "source": "HR"
                }
            )

        employees = User.objects.filter(employeeprofile__isnull=False)
        Notification.objects.bulk_create([
            Notification(
                to_user=emp,
                title=f"New Announcement: {announcement.title}",
                body=announcement.description,
                notif_type="announcement",
                extra={"announcement_id": announcement.id}
            )
            for emp in employees
        ])

        return Response({
            "success": True,
            "message": "Announcement created",
            "data": serializer.data
        }, status=201)

    return Response(serializer.errors, status=400)


class SalaryStructureListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.SalaryStructureSerializer
    queryset = SalaryStructure.objects.all()


class EmployeeSalaryAssignAPIView(APIView):
    permission_classes = [IsAuthenticated, IsHR]

    def post(self, request, profile_id):
        prof = get_object_or_404(EmployeeProfile, id=profile_id)
        struct_id = request.data.get('structure_id')
        eff_from = request.data.get('effective_from')
        struct = get_object_or_404(SalaryStructure, id=struct_id)
        es, created = EmployeeSalary.objects.update_or_create(
            profile=prof, defaults={'structure': struct, 'effective_from': eff_from})
        return Response(serializers.EmployeeSalaryAdminSerializer(es).data)


class MyPayrollDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        salary = (
            EmployeeSalary.objects
            .filter(profile__user=user, is_active=True)
            .order_by("-effective_from")
            .first()
        )

        if not salary:
            return Response({"salary": None}, status=200)

        serializer = MySalaryDetailSerializer(salary)
        return Response({"salary": serializer.data}, status=200)


class HRGeneratePayslipAPIView(APIView):
    permission_classes = [IsAuthenticated, IsHR]

    def post(self, request, profile_id):
        profile = get_object_or_404(EmployeeProfile, id=profile_id)

        year = int(request.data.get('year'))
        month = int(request.data.get('month'))

        es = profile.salary
        structure = es.structure

        # --- Working days (Mon–Fri) ---
        cal = calendar.Calendar()
        working_days = sum(
            1 for d in cal.itermonthdays2(year, month)
            if d[0] != 0 and d[1] < 5
        )

        attendances = Attendance.objects.filter(
            user=profile.user,
            date__year=year,
            date__month=month,
            status='completed'
        )

        days_present = attendances.count()
        absent_days = working_days - days_present

        # --- Salary breakup ---
        monthly_gross = float(structure.monthly_ctc)

        prorata_gross = (
            monthly_gross * (days_present / working_days)
            if working_days else 0
        )

        basic = structure.basic_amount()
        hra = structure.hra_amount()
        pf = structure.pf_amount()

        professional_tax = 200
        insurance = float(request.data.get('insurance', 0))
        esi = float(request.data.get('esi', 0))

        # --- Overtime ---
        overtime_seconds = attendances.aggregate(
            total=Sum('overtime_seconds')
        )['total'] or 0

        hourly_rate = es.hourly_rate(working_days)
        overtime_amount = (
            (overtime_seconds / 3600) *
            hourly_rate *
            float(structure.overtime_multiplier)
        )

        total_deductions = pf + professional_tax + insurance + esi
        net_amount = prorata_gross + overtime_amount - total_deductions

        payslip, _ = Payslip.objects.update_or_create(
            profile=profile,
            year=year,
            month=month,
            defaults={
                'working_days': working_days,
                'days_present': days_present,
                'gross_amount': round(prorata_gross, 2),
                'overtime_amount': round(overtime_amount, 2),
                'deductions': round(total_deductions, 2),
                'net_amount': round(net_amount, 2),
                'details': {
                    'monthly_ctc': monthly_gross,
                    'basic': round(float(basic), 2),
                    'hra': round(float(hra), 2),
                    'pf': round(float(pf), 2),
                    'professional_tax': professional_tax,
                    'insurance': insurance,
                    'esi': esi,
                    'absent_days': absent_days,
                    'overtime_amount': round(overtime_amount, 2)
                },
                'generated_by': request.user
            }
        )

        return Response(
            serializers.PayslipAdminSerializer(payslip).data,
            status=201
        )


class HRLeaveListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.LeaveRequestAdminSerializer

    def get_queryset(self):
        q = LeaveRequest.objects.all().select_related('profile')
        status = self.request.query_params.get('status')
        if status:
            q = q.filter(status=status)
        return q


class HRLeaveDetailAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.LeaveRequestAdminSerializer
    queryset = LeaveRequest.objects.all()


class HRLeaveActionAPIView(APIView):
    permission_classes = [IsAuthenticated, IsHR]

    def post(self, request, leave_id):
        action = request.data.get('action')
        remarks = request.data.get('remarks', '')

        if not action:
            return Response(
                {"detail": "Action is required. Use 'approve or 'reject'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if action not in ['approve', 'reject']:
            return Response(
                {"detail": "Invalid action. Allowed values: approve, reject."},
                status=status.HTTP_400_BAD_REQUEST
            )

        lr = get_object_or_404(LeaveRequest, id=leave_id)

        # 🔒 If TL exists, HR must wait for TL approval
        if lr.tl is not None and lr.status != "tl_approved":
            return Response(
                {"detail": "TL approval required before HR action."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            if action == 'approve':
                lr.apply_hr_approval(
                    request.user,
                    approve=True,
                    remarks=remarks
                )

                try:
                    lb = LeaveBalance.objects.get(
                        profile=lr.profile, leave_type=lr.leave_type)
                    lb.used += lr.days
                    lb.save()
                except LeaveBalance.DoesNotExist:
                    pass

                Notification.objects.create(
                    to_user=lr.profile.user,
                    title='Leave approved',
                    body=remarks or 'Your leave approved by HR',
                    notif_type='leave',
                    extra={'leave_id': lr.id}
                )

                return Response(
                    {'detail': 'Leave approved by HR'},
                    status=status.HTTP_200_OK
                )

            else:
                lr.apply_hr_approval(
                    request.user,
                    approve=False,
                    remarks=remarks
                )

                Notification.objects.create(
                    to_user=lr.profile.user,
                    title='Leave rejected',
                    body=remarks or 'Your leave rejected by HR',
                    notif_type='leave',
                    extra={'leave_id': lr.id}
                )

                return Response(
                    {'detail': 'Leave rejected by HR'},
                    status=status.HTTP_200_OK
                )

        except ValidationError as e:
            return Response(
                e.message_dict if hasattr(e, "message_dict") else {
                    "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class HRDashboardStatsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsHR]

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
        on_leave_employees = LeaveRequest.objects.filter(
            start_date__lte=today,
            end_date__gte=today,
            status__in=['hr_approved', 'tl_approved']
        ).count()

        return Response({
            "total_employees": total_employees,
            "present_employees": present_employees,
            "on_leave_employees": on_leave_employees
        })


class HRLeaveDashboardStatsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsHR]

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
        # Note: This is used to calculate absent employees
        on_leave_employees = LeaveRequest.objects.filter(
            start_date__lte=today,
            end_date__gte=today,
            status__in=['hr_approved', 'tl_approved']
        ).count()

        # 4. Absent Employees (Total - Present - On Leave)
        absent_employees = total_employees - present_employees - on_leave_employees
        if absent_employees < 0:
            absent_employees = 0

        # 5. Pending Leave Requests (Awaiting HR action)
        pending_leaves = LeaveRequest.objects.filter(
            status__in=['applied', 'tl_approved']
        ).count()

        return Response({
            "present_today": present_employees,
            "absent_today": absent_employees,
            "leave_requests": pending_leaves
        })
