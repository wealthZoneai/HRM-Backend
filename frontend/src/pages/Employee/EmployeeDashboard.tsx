import DashboardLayout from "../../components/dashboard/DashboardLayout";
import TimeCard  from "../../components/dashboard/TimeCard";
import AttendanceStat from "../../components/dashboard/AttendanceStat";
import PerformanceChart from "../../components/dashboard/PerformanceChart";
import AttendanceChart from "../../components/dashboard/AttendanceChart";
import Announcements from "../../components/dashboard/Announcements";
import { UpcomingHolidays } from "../../components/dashboard/UpcomingHolidays";
import LeaveRequests from "../../components/dashboard/LeaveRequests";

export default function EmployeeDashboard() {
  return (
    <DashboardLayout>
      <div className="space-y-6">

        {/* Top Greeting + Search */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold">Hello Ravi Teja</h1>
            <p className="text-gray-500 text-sm">Monday, 22 March 2025</p>
          </div>
          <input
            type="text"
            className="border rounded-lg px-4 py-2 w-80"
            placeholder="Search here"
          />
        </div>

        {/* Time In/Out + Attendance Summary */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <TimeCard label="Time In" time="9:00 AM" actionLabel="Clock in" />
          <TimeCard label="Time Out" time="7:00 PM" actionLabel="Clock out" />

          <AttendanceStat title="Total Attendance" value={80} />
          <AttendanceStat title="On Time %" value={95} />
        </div>

        {/* Performance + Attendance Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <PerformanceChart />
          <AttendanceChart />
        </div>

        {/* Bottom Grid: Announcements, Holidays, Leaves */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Announcements />
          <UpcomingHolidays />
          <LeaveRequests />
        </div>

      </div>
    </DashboardLayout>
  );
}
