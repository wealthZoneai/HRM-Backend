# hr/views.py
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from emp.models import EmployeeProfile, Shift, Attendance, CalendarEvent, SalaryStructure, EmployeeSalary, Payslip, LeaveRequest, LeaveType, LeaveBalance
from . import serializers
from .permissions import IsHR, IsTL
from django.db.models import Sum, Count
from django.utils import timezone
import calendar
from django.contrib.auth import get_user_model
from . import models
from .serializers import AnnouncementSerializer, MySalaryDetailSerializer
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from .serializers import AnnouncementSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Announcement
from tl.serializers import TLAnnouncementSerializer




User = get_user_model()

# --- Employee listing & detail (HR) ---


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

# --- Attendance admin endpoints ---


class HRAttendanceListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.AttendanceAdminSerializer

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        month = self.request.query_params.get('month')
        qs = Attendance.objects.all().select_related('user', 'shift')
        if user_id:
            qs = qs.filter(user__id=user_id)
        if month:
            y, m = map(int, month.split('-'))
            qs = qs.filter(date__year=y, date__month=m)
        return qs.order_by('-date')


class HRAttendanceRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    queryset = Attendance.objects.all()
    serializer_class = serializers.AttendanceAdminSerializer


class HRAttendanceCorrectAPIView(APIView):
    permission_classes = [IsAuthenticated, IsHR]

    def post(self, request, attendance_id):
        att = get_object_or_404(Attendance, id=attendance_id)
        new_ci = request.data.get('clock_in')
        new_co = request.data.get('clock_out')
        note = request.data.get('note', 'Corrected by HR')
        if new_ci:
            att.clock_in = new_ci
        if new_co:
            att.clock_out = new_co
        att.note = (att.note or '') + f"\nHR correction: {note}"
        att.manual_entry = True
        att.status = 'completed' if att.clock_out else att.status
        att.compute_duration_and_overtime()
        att.save()
        return Response(serializers.AttendanceAdminSerializer(att).data)

# --- Shift management ---


class ShiftListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.ShiftSerializer
    queryset = Shift.objects.all()


class ShiftRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.ShiftSerializer
    queryset = Shift.objects.all()

# --- Calendar & announcements (HR create) ---


class HRCalendarCreateAPIView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.CalendarEventSerializer
    queryset = CalendarEvent.objects.all()


# hr/views.py

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import Announcement
from .serializers import AnnouncementSerializer

from emp.models import Notification
from django.contrib.auth import get_user_model
User = get_user_model()


# --------------------------------------------------------
# 1. CREATE ANNOUNCEMENT  (POST)
# --------------------------------------------------------
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_announcement(request):
    serializer = AnnouncementSerializer(data=request.data)
    if serializer.is_valid():
        announcement = serializer.save(created_by=request.user)

        # ---- CREATE NOTIFICATIONS HERE ----
        employees = User.objects.filter(role__icontains="emp")

        for emp in employees:
            Notification.objects.create(
                to_user=emp,
                title=f"New Announcement: {announcement.title}",
                body=f"HR added a new announcement: {announcement.title}",
                notif_type="announcement",
                extra={"announcement_id": announcement.id}
            )
        # -------------------------------------

        return Response({
            "success": True,
            "message": "Announcement created successfully",
            "data": serializer.data
        })



# --------------------------------------------------------
# 2. LIST ANNOUNCEMENTS (GET)
# --------------------------------------------------------
@csrf_exempt
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

@api_view(['PUT','PATCH'])

# --------------------------------------------------------
# 3. UPDATE ANNOUNCEMENT (PUT/PATCH)
# --------------------------------------------------------
@api_view(['PUT', 'PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated , IsHR])
def update_announcement(request,pk):
@permission_classes([IsAuthenticated])
def update_announcement(request, pk):
    try:
        announcement_data = Announcement.objects.get(pk=pk)
    except Announcement.DoesNotExist:
        return Response({"error":"Announcement not found"},status=404)
    serializer = AnnouncementSerializer(
        announcement_data,
        data=request.data,
        partial=True
    )
        return Response({"error": "Announcement not found"}, status=404)

    serializer = AnnouncementSerializer(announce, data=request.data, partial=True)
    if serializer.is_valid():
        updated_announcement = serializer.save()
        employees = User.objects.filter(employeeprofile__isnull=False)
        announcement = serializer.save()

        # ---- CREATE NOTIFICATIONS HERE ----
        employees = User.objects.filter(role__icontains="emp")

        for emp in employees:
            Notification.objects.create(
                to_user=emp,
                title="announcement updated",
                body="The announcement"+updated_announcement.title+"was updated",
                notif_type="announcement",
                extra={"announcement_id":updated_announcement.id}
            )
        return Response({
        "success":True,
        "data":serializer.data
        })
    return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        # -------------------------------------

        return Response({"success": True, "data": serializer.data})



# --------------------------------------------------------
# 4. DELETE ANNOUNCEMENT (DELETE)
# --------------------------------------------------------
@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_announcement(request, pk):
    try:
        announcement_data = Announcement.objects.get(pk=pk)
    except Announcement.DoesNotExist:
        return Response({"error": "Announcement not found"}, status=404)
    announcement_title = announcement_data.title
    announcement_data.delete() 
    employees = User.objects.filter(employeeprofile__isnull=False)

    title = announce.title
    announce.delete()

    # ---- CREATE NOTIFICATIONS HERE ----
    employees = User.objects.filter(role__icontains="emp")

    for emp in employees:
        Notification.objects.create(
            to_user=emp,
            title="Announcement Deleted",
            body=f"The Announcement"+announcement_title+"was deleted.",
            notif_type="announcement"
        )
    # -------------------------------------

    return Response({"success": True, "message": "Deleted successfully"})




from tl.models import TLAnnouncement
from hr.serializers import TLAnnouncementSerializer

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def emp_tl_announcements(request):
#     profile = EmployeeProfile.objects.filter(
#         user=request.user).select_related('team_lead').first()
#     if not profile:
#         return Response({"message": "No profile found for user"}, status=404)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def emp_tl_announcements(request):
    profile = EmployeeProfile.objects.get(user=request.user)

#     tl = profile.team_lead
#     if not tl:
#         return Response({"message": "No Team Lead assigned"}, status=200)
    # Employee’s assigned Team Lead
    tl = profile.team_lead

    if tl is None:
        return Response({"message": "No Team Lead assigned"}, status=200)

#     announcements = TLAnnouncement.objects.filter(created_by=tl)
#     serializer = TLAnnouncementSerializer(announcements, many=True)
#     return Response(serializer.data)
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
        notification_list = []
        for emp in employees:
            notification = Notification(
                to_user=emp,
                title="New Announcement: " + announcement.title,
                body=announcement.description,
                notif_type="announcement",
                extra={"announcement_id": announcement.id}
            )
            notification_list.append(notification)
        Notification.objects.bulk_create(notification_list)
        return Response({
            "success": True,
            "message": "Announcement created successfully",
            "data": serializer.data
        }, status=201)
    return Response(serializer.errors, status=400)




# --- Salary / Payslip admin --- 
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
 
 
class HRGeneratePayslipAPIView(APIView):
    permission_classes = [IsAuthenticated, IsHR]
 
    def post(self, request, profile_id):
        # body: year, month, force (bool)
        profile = get_object_or_404(EmployeeProfile, id=profile_id)
        year = int(request.data.get('year', timezone.localdate().year))
        month = int(request.data.get('month', timezone.localdate().month))
        force = bool(request.data.get('force', False))
 
        # validate salary assigned
        try:
            es = profile.salary
        except EmployeeSalary.DoesNotExist:
            return Response({"detail": "No salary assigned"}, status=400)
 
        # working days (Mon-Fri)
        cal = calendar.Calendar()
        working_days = sum(1 for d in cal.itermonthdays2(
            year, month) if d[0] != 0 and d[1] < 5)
 
        attend_qs = Attendance.objects.filter(
            user=profile.user, date__year=year, date__month=month, status='completed')
        days_present = attend_qs.count()
        total_seconds = attend_qs.aggregate(
            total=Sum('duration_time'))['total'] or 0
        overtime_seconds = attend_qs.aggregate(
            total=Sum('overtime_seconds'))['total'] or 0
 
        gross = float(es.structure.monthly_ctc)
        prorata = gross * \
            (days_present / working_days) if working_days else 0.0
 
        hourly_rate = es.hourly_rate(working_days_in_month=working_days)
        overtime_amt = (overtime_seconds / 3600.0) * \
            hourly_rate * float(es.structure.overtime_multiplier)
 
        # HR can pass extra deductions
        deductions = float(request.data.get('deductions', 0.0))
        net = prorata + overtime_amt - deductions
 
        payslip, created = Payslip.objects.update_or_create(
            profile=profile, year=year, month=month,
            defaults={
                'working_days': working_days,
                'days_present': days_present,
                'gross_amount': round(prorata, 2),
                'overtime_amount': round(overtime_amt, 2),
                'deductions': round(deductions, 2),
                'net_amount': round(net, 2),
                'details': {
                    'monthly_ctc': es.structure.monthly_ctc,
                    'prorata': round(prorata, 2),
                    'overtime_amt': round(overtime_amt, 2),
                    'deductions': round(deductions, 2)
                },
                'generated_by': request.user
            }
        )
        return Response(serializers.PayslipAdminSerializer(payslip).data, status=201 if created else 200)

# --- Leave admin actions and listings ---


class HRLeaveListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.LeaveRequestAdminSerializer

    def get_queryset(self):
        q = LeaveRequest.objects.all().select_related('profile', 'leave_type')
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
        action = request.data.get('action')  # 'approve' or 'reject'
        remarks = request.data.get('remarks', '')
        lr = get_object_or_404(LeaveRequest, id=leave_id)
        if action == 'approve':
            lr.apply_hr_approval(request.user, approve=True, remarks=remarks)
            # deduct balance
            try:
                lb = LeaveBalance.objects.get(
                    profile=lr.profile, leave_type=lr.leave_type)
                lb.used = lb.used + lr.days
                lb.save()
            except LeaveBalance.DoesNotExist:
                pass
            # notify employee
            # create notification
            models.Notification.objects.create(to_user=lr.profile.user, title='Leave approved',
                                               body=remarks or 'Your leave approved by HR', notif_type='leave', extra={'leave_id': lr.id})
            return Response({'detail': 'approved'})
        else:
            lr.apply_hr_approval(request.user, approve=False, remarks=remarks)
            models.Notification.objects.create(to_user=lr.profile.user, title='Leave rejected',
                                               body=remarks or 'Your leave rejected by HR', notif_type='leave', extra={'leave_id': lr.id})
            return Response({'detail': 'rejected'})
