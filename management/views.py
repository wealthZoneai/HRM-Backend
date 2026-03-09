from datetime import date, time
import calendar

from django.utils import timezone
from django.utils.timezone import now
from django.db.models import Count, Sum, Case, When, FloatField, Value
from django.contrib.auth import get_user_model

from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from management.models import LongLeave
from emp.models import LeaveRequest, Attendance, EmployeeProfile


User = get_user_model()


# ==============================
# TOTAL EMPLOYEES
# ==============================

class ADMINTotalEmployeesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        employees = EmployeeProfile.objects.filter(is_active=True)

        return Response({
            "current_total": employees.count(),
            "personnel_directory": employees.values(
                "emp_id",
                "first_name",
                "last_name",
                "department",
                "designation",
                "role"
            )
        })


# ==============================
# EMPLOYEES ON LEAVE TODAY
# ==============================

class ADMINOnLeaveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        today = date.today()

        leaves = LeaveRequest.objects.filter(
            status="hr_approved",
            start_date__lte=today,
            end_date__gte=today
        ).select_related("profile__user")

        return Response({
            "current_total": leaves.count(),
            "active_leave_requests": [
                {
                    "employee_name": leave.profile.user.get_full_name(),
                    "leave_type": leave.leave_type,
                    "days": leave.days
                }
                for leave in leaves
            ]
        })


# ==============================
# PENDING LEAVE REQUESTS
# ==============================

class ADMINPendingRequestsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        pending_leaves = LeaveRequest.objects.filter(
            status__in=["applied", "tl_approved", "pending_hr"]
        ).select_related("profile__user")

        return Response({
            "current_total": pending_leaves.count(),
            "pending_requests": [
                {
                    "employee_name": leave.profile.user.get_full_name(),
                    "leave_type": leave.leave_type,
                    "applied_date": leave.applied_at.date()
                }
                for leave in pending_leaves
            ]
        })


# ==============================
# LONG LEAVE DASHBOARD
# ==============================

@api_view(["GET"])
def admin_long_leave_dashboard(request):

    total_long_leave = LongLeave.objects.filter(is_active=True).count()

    breakdown = (
        LongLeave.objects
        .filter(is_active=True)
        .values("leave_type")
        .annotate(total=Count("id"))
    )

    department_status = [
        {
            "leave_type": item["leave_type"],
            "count": item["total"]
        }
        for item in breakdown
    ]

    employees = LongLeave.objects.filter(is_active=True).select_related("employee")

    employee_list = [
        {
            "employee_name": emp.employee.first_name,
            "status": emp.status,
            "reason": emp.leave_type,
            "duration": emp.duration_days,
            "start_date": emp.start_date,
            "end_date": emp.end_date,
            "document_type": emp.document_type,
            "additional_note": emp.note
        }
        for emp in employees
    ]

    return Response({
        "overview": {
            "current_value": total_long_leave
        },
        "department_status": department_status,
        "employees_on_long_leave": employee_list
    })


# ==============================
# LATE ARRIVALS TODAY
# ==============================

class ADMINLateArrivalsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        today = timezone.localdate()
        late_time = time(9, 45)

        records = Attendance.objects.filter(
            date=today,
            late_arrivals=True
        ).select_related("user", "user__employeeprofile")

        employees = []

        for record in records:

            clock_in = timezone.localtime(record.clock_in)

            late_minutes = (
                (clock_in.hour * 60 + clock_in.minute) -
                (late_time.hour * 60 + late_time.minute)
            )

            employees.append({
                "employee_name": record.user.first_name,
                "department": getattr(record.user.employeeprofile, "department", None),
                "clock_in": clock_in.strftime("%I:%M %p"),
                "late_display": f"{late_minutes}m Late"
            })

        return Response({
            "current_total": len(employees),
            "late_policy": "After 09:45 AM",
            "late_employees_today": employees
        })


# ==============================
# LEAVE TYPE BREAKDOWN
# ==============================

class ADMINLeaveTypeBreakdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        allowed_types = ["CASUAL", "SICK", "PAID", "UNPAID"]

        breakdown = (
            LeaveRequest.objects
            .filter(status="approved", leave_type__in=allowed_types)
            .values("leave_type")
            .annotate(total=Count("profile", distinct=True))
        )

        result = {
            "Casual Leave": 0,
            "Sick Leave": 0,
            "Paid Leave": 0,
            "Unpaid Leave": 0,
        }

        for item in breakdown:
            key = dict(LeaveRequest.LEAVE_TYPE_CHOICES).get(item["leave_type"])
            result[key] = item["total"]

        return Response({"leave_type_breakdown": result})


# ==============================
# EMPLOYEES ON LEAVE - DEPT WISE
# ==============================

class ADMINEmployeesOnLeaveDeptWiseAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        today = now().date()

        departments = [
            "Python", "QA", "Java", "UI/UX", "React",
            "Cyber Security", "Digital Marketing",
            "HR", "BDM", "Networking", "Cloud"
        ]

        dept_counts = {dept: 0 for dept in departments}

        leave_profiles = LeaveRequest.objects.filter(
            status="approved",
            start_date__lte=today,
            end_date__gte=today
        ).values_list("profile", flat=True)

        dept_breakdown = (
            EmployeeProfile.objects
            .filter(id__in=leave_profiles)
            .values("department")
            .annotate(total=Count("id"))
        )

        for item in dept_breakdown:
            dept_counts[item["department"]] = item["total"]

        result = [
            {"department": dept, "total": count}
            for dept, count in dept_counts.items()
        ]

        return Response({
            "employees_on_leave_dept_wise": result
        })


# ==============================
# ATTENDANCE TREND
# ==============================

class ADMINAttendanceTrendAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        current_year = now().year
        total_employees = User.objects.count()

        monthly_data = {}

        for month in range(1, 13):

            days = calendar.monthrange(current_year, month)[1]
            total_possible = total_employees * days

            attendance = Attendance.objects.filter(
                date__year=current_year,
                date__month=month
            )

            effective_present = attendance.aggregate(
                total=Sum(
                    Case(
                        When(status="present", then=Value(1)),
                        When(status="halfday", then=Value(0.5)),
                        default=Value(0),
                        output_field=FloatField()
                    )
                )
            )["total"] or 0

            percentage = round(
                (effective_present / total_possible) * 100, 2
            ) if total_possible > 0 else 0

            monthly_data[calendar.month_abbr[month]] = percentage

        return Response({
            "attendance_trend_percentage": monthly_data
        })


# ==============================
# TOTAL PRESENT TODAY
# ==============================

@api_view(["GET"])
def total_present_api(request):

    today = now().date()

    total_present = Attendance.objects.filter(
        date=today,
        status="present"
    ).count()

    total_employees = EmployeeProfile.objects.count()

    departments = EmployeeProfile.objects.values("department").distinct()

    department_list = []

    for dept in departments:

        dept_name = dept["department"]

        total = EmployeeProfile.objects.filter(
            department=dept_name
        ).count()

        present = Attendance.objects.filter(
            user__employeeprofile__department=dept_name,
            date=today,
            status="present"
        ).count()

        department_list.append({
            "department": dept_name,
            "present": present,
            "total": total
        })

    return Response({
        "total_present": total_present,
        "total_employees": total_employees,
        "departments": department_list
    })


    from emp.models import EmployeeProfile
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count
from django.utils.timezone import now
from django.db.models.functions import TruncMonth
from .serializers import NewJoineeSerializer
 
 
class TotalEmployeesAPIView(APIView):
 
    def get(self, request):
 
        total = EmployeeProfile.objects.count()
 
        full_time = EmployeeProfile.objects.filter(
            employment_type="Full-Time"
        ).count()
 
        contract = EmployeeProfile.objects.filter(
            employment_type="Contract"
        ).count()
 
        return Response({
            "total_employees": total,
            "full_time": full_time,
            "contract": contract
        })
   
class AnnualGrowthAPIView(APIView):
 
    def get(self, request):
 
        current_year = now().year
        last_year = current_year - 1
 
        current = EmployeeProfile.objects.filter(
            joining_date__year=current_year
        ).count()
 
        last = EmployeeProfile.objects.filter(
            joining_date__year=last_year
        ).count()
 
        growth = 0
 
        if last > 0:
            growth = ((current - last) / last) * 100
 
        return Response({
            "current_year": current,
            "last_year": last,
            "growth_percentage": round(growth, 2)
        })
   
class NewJoineesAPIView(APIView):
 
    def get(self, request):
 
        employees = EmployeeProfile.objects.order_by(
            "-joining_date"
        )[:10]
 
        serializer = NewJoineeSerializer(employees, many=True)
 
        return Response(serializer.data)
   
 
class DepartmentHeadcountAPIView(APIView):
 
    def get(self, request):
 
        departments = (
            EmployeeProfile.objects
            .values("department")
            .annotate(headcount=Count("id"))
            .order_by("-headcount")
        )
 
        data = []
 
        for dept in departments:
            data.append({
                "department": dept["department"],
                "headcount": dept["headcount"]
            })
 
        return Response(data)
   
class MonthlyEmployeeChartAPIView(APIView):
 
    def get(self, request):
 
        data = (
            EmployeeProfile.objects
            .annotate(month=TruncMonth("joining_date"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
 
        result = []
 
        for item in data:
            result.append({
                "month": item["month"].strftime("%b %Y"),
                "count": item["count"]
            })
 
        return Response(result)
   
   # ceo/views.py
 
from emp.models import EmployeeProfile
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count
from django.utils.timezone import now
from django.db.models.functions import TruncMonth
from .serializers import NewJoineeSerializer
 
 
class TotalEmployeesAPIView(APIView):
 
    def get(self, request):
 
        total = EmployeeProfile.objects.count()
 
        full_time = EmployeeProfile.objects.filter(
            employment_type="Full-Time"
        ).count()
 
        contract = EmployeeProfile.objects.filter(
            employment_type="Contract"
        ).count()
 
        return Response({
            "total_employees": total,
            "full_time": full_time,
            "contract": contract
        })
   
class AnnualGrowthAPIView(APIView):
 
    def get(self, request):
 
        current_year = now().year
        last_year = current_year - 1
 
        current = EmployeeProfile.objects.filter(
            date_of_joining__year=current_year
        ).count()
 
        last = EmployeeProfile.objects.filter(
            date_of_joining__year=last_year
        ).count()
 
        growth = 0
 
        if last > 0:
            growth = ((current - last) / last) * 100
 
        return Response({
            "current_year": current,
            "last_year": last,
            "growth_percentage": round(growth, 2)
        })
   
class NewJoineesAPIView(APIView):

    def get(self, request):

        current_year = now().year
        current_month = now().month

        new_joinees = EmployeeProfile.objects.filter(
            date_of_joining__year=current_year,
            date_of_joining__month=current_month
        ).order_by("-date_of_joining")

        employees = []

        for emp in new_joinees:
            employees.append({
                "id": emp.id,
                "name": f"{emp.first_name} {emp.last_name}",
                "department": emp.department,
                "designation": emp.designation,
                "date_of_joining": emp.date_of_joining
            })

        return Response({
            "count": new_joinees.count(),
            "employees": employees
        })
   
 
class DepartmentHeadcountAPIView(APIView):
 
    def get(self, request):
 
        departments = (
            EmployeeProfile.objects
            .values("department")
            .annotate(headcount=Count("id"))
            .order_by("-headcount")
        )
 
        data = []
 
        for dept in departments:
            data.append({
                "department": dept["department"],
                "headcount": dept["headcount"]
            })
 
        return Response(data)
   
class MonthlyEmployeeChartAPIView(APIView):
    def get(self, request):
        monthly_data = (
            EmployeeProfile.objects
            .exclude(date_of_joining__isnull=True)   # ✅ remove null dates
            .annotate(month=TruncMonth("date_of_joining"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
        result = []
        for item in monthly_data:
            result.append({
                "month": item["month"].strftime("%b %Y"),
                "count": item["count"]
            })
        return Response(result)
   
class DepartmentEmployeeAPIView(APIView):
 
    def get(self, request):
 
        department_data = (
            EmployeeProfile.objects
            .values("department")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
 
        data = []
 
        for dept in department_data:
            data.append({
                "department": dept["department"],
                "count": dept["count"]
            })
 
        return Response(data)
 
 
from rest_framework.views import APIView

from rest_framework.response import Response

from django.utils.timezone import now
 
from emp.models import EmployeeProfile

from .serializers import NewJoineesMonthSerializer
 
 
class NewJoineesThisMonthAPIView(APIView):
 
    def get(self, request):
 
        current_year = now().year

        current_month = now().month
 
        employees = EmployeeProfile.objects.filter(

            date_of_joining__year=current_year,

            date_of_joining__month=current_month

        ).order_by("-date_of_joining")
 
        serializer = NewJoineesMonthSerializer(employees, many=True)
 
        return Response({

            "count": employees.count(),

            "employees": serializer.data

        })
 
#attrion 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.db.models import Count
from django.db.models.functions import ExtractMonth
from datetime import datetime

from emp.models import EmployeeProfile
from .permissions import Ismanagement


class adminAttritionDashboardAPIView(APIView):

    permission_classes = [IsAuthenticated, Ismanagement]

    def get(self, request):

        # total employees
        total_employees = EmployeeProfile.objects.count()

        # employees who left
        inactive_employees = EmployeeProfile.objects.filter(is_active=False)

        inactive_count = inactive_employees.count()

        # attrition rate
        if total_employees > 0:
            attrition_rate = (inactive_count / total_employees) * 100
        else:
            attrition_rate = 0

        # current month attrition
        now = datetime.now()

        this_month = inactive_employees.filter(
            updated_at__month=now.month,
            updated_at__year=now.year
        ).count()

        # yearly attrition
        yearly_attrition = inactive_employees.filter(
            updated_at__year=now.year
        ).count()

        # highest attrition department
        department_data = (
            inactive_employees
            .values('department')
            .annotate(total=Count('id'))
            .order_by('-total')
        )

        highest_department = department_data.first()

        # monthly trend
        monthly_trend = (
            inactive_employees
            .annotate(month=ExtractMonth('updated_at'))
            .values('month')
            .annotate(total=Count('id'))
            .order_by('month')
        )

        # attrition reasons
        reasons = (
            inactive_employees
            .values('exit_reason')
            .annotate(total=Count('id'))
        )

        data = {

            "current_attrition_rate": round(attrition_rate, 2),

            "attrition_this_month": this_month,

            "total_attrition_ytd": yearly_attrition,

            "highest_attrition_department": highest_department,

            "attrition_trend_by_month": monthly_trend,

            "top_departments_with_attrition": department_data,

            "attrition_reasons": reasons

        }

        return Response(data)