# HRMS API — Developer Reference

Generated sections: LOGIN, EMP (Employee), HR (Human Resources), TL (Team Lead)

---
## Authentication (common)
- All endpoints that require authentication use JWT via Authorization: Bearer <token>
- Date formats: `YYYY-MM-DD` for dates, ISO 8601 for datetimes where applicable.
- Timezone: Asia/Kolkata

---
# LOGIN APP

## POST /login/forgot-password/
Permissions: AllowAny
Request JSON:
```json
{ "email": "user@example.com" }
```
Response 200 (always returns success to prevent enumeration):
```json
{ "email": "user@example.com" }
```

## POST /login/verify-otp/
Permissions: AllowAny
Request JSON:
```json
{ "email": "user@example.com", "otp": "123456" }
```
Response 200/201:
```json
{ "email": "user@example.com", "otp": "123456" }
```

## POST /login/reset-password/
Permissions: AllowAny
Request JSON:
```json
{
  "email": "user@example.com",
  "otp": "123456",
  "new_password": "NewP@ssw0rd",
  "confirm_password": "NewP@ssw0rd"
}
```
Response 200:
```json
{ "email": "user@example.com" }
```

## POST /login/token/ (JWT token obtain)
Permissions: AllowAny
Request JSON:
```json
{ "username": "user", "password": "pass" }
```
Response 200:
```json
{ "access": "<jwt>", "refresh": "<jwt>" }
```

## POST /login/token/refresh/
Permissions: AllowAny
Request JSON:
```json
{ "refresh": "<refresh_token>" }
```

---
# EMP APP

Base path prefix: `/emp/` (examples below)

## GET /emp/my-profile/
Permissions: Authenticated
Response:
```json
{ "user": { "id": 1, "username":"...","email":"...","role":"employee" }, "emp_id":"WZG-AI-0001", ... }
```

## PATCH /emp/my-profile/contact/
Permissions: Authenticated
Request: multipart/form-data or JSON with fields in ContactSerializer:
- first_name, middle_name, last_name, personal_email, phone_number, alternate_number, dob, blood_group, gender, marital_status, profile_photo
Response: updated profile JSON

## PATCH /emp/my-profile/identification/
Permissions: Authenticated
Request: identification fields (aadhaar_number, aadhaar_image, pan_number, pan_image, passport_number, passport_image)

## GET /emp/dashboard/summary/
Permissions: Authenticated
Query params: `month=YYYY-MM` (optional)
Response: attendance_today, monthly_summary, announcements, leave_summary, upcoming_holidays

## POST /emp/attendance/clock-in/
Permissions: Authenticated
Creates today's attendance with clock_in = now. Error if already exists.

## POST /emp/attendance/clock-out/
Permissions: Authenticated
Sets clock_out = now and computes duration. Errors if not clocked in or already clocked out.

## GET /emp/attendance/days/?month=YYYY-MM
Permissions: Authenticated
List user's attendance days (last 30 by default).

## GET /emp/calendar/?year=YYYY&month=MM
Permissions: Authenticated
List calendar events for month

## GET /emp/announcements/
Permissions: Authenticated
Returns HR announcements list

## GET /emp/notifications/?unread=true
Permissions: Authenticated
List notifications for user

## POST /emp/notifications/mark-read/
Permissions: Authenticated
Body: `{ "ids": [1,2,3] }` marks notifications read

## GET /emp/tl-announcements/
Permissions: Authenticated
Returns announcements created by the employee's team lead

## GET /emp/payroll/my-details/
Permissions: Authenticated
Returns salary details if exists

## GET /emp/payroll/my-payslips/
Permissions: Authenticated
List payslips

## GET /emp/payroll/my-payslips/{year}/{month}/download/
Permissions: Authenticated
Returns a download URL for payslip PDF

## GET /emp/leave/my-balance/
Permissions: Authenticated
Returns leave balances for logged user

## GET /emp/leave/my-requests/
Permissions: Authenticated
List leave requests for logged user

## POST /emp/leave/apply/
Permissions: Authenticated
Request body: `leave_type`, `start_date`, `end_date`, `reason` (optional)
Behavior: validates overlap, balance, routes to TL or HR depending on TL availability

## Policy endpoints
- GET /emp/policy/ (list)
- POST /emp/policy/create/ (HROrManagement)
- GET /emp/policy/{pk}/ (detail)
- PUT/PATCH/DELETE /emp/policy/{pk}/ (HROrManagement for update/delete)

## HR Create Employee (multipart)
POST /emp/hr/create-employee/
Permissions: IsHROrManagement
Accepts multipart/form-data with nested `contact`, `job`, `bank`, `identification` JSON fields or file fields prefixed like `contact.profile_photo`

## Leave action (TL/HR)
POST /emp/action/leave/{leave_id}/
Permissions: IsTLorHRorOwner
Body: `{ "action": "approve" | "reject", "remarks": "..." }`

## Timesheet endpoints (employee)
- GET /emp/timesheet/daily/form/  -> returns today's timesheet and existing entries
- POST /emp/timesheet/daily/update/ -> payload `entries` array of {start_time, end_time, task, description}

## Timesheet endpoints (HR/TL)
- GET /emp/timesheet/hr/daily/?emp_id=...&date=YYYY-MM-DD
- GET /emp/timesheet/hr/monthly/?emp_id=...&month=YYYY-MM
- GET /emp/timesheet/hr/worksheet/?emp_id=...&from=YYYY-MM-DD&to=YYYY-MM-DD
- GET /emp/timesheet/hr/yearly/?emp_id=...&year=YYYY
- GET /emp/timesheet/tl/... (same patterns for TL)

---
# HR APP

Base: `/hr/`

## Announcement endpoints
- GET /hr/announcements/  (list) — Authenticated
- POST /hr/announcement/create/ — Permissions: IsHR
  Request: AnnouncementSerializer fields (title, body, date, audience)
- PUT/PATCH /hr/announcement/{id}/ — IsHR
- DELETE /hr/announcement/{id}/ — IsHR

## TL announcements (TL management)
- POST /hr/tl/announcement/create/ — Permissions: IsTL, uses TLAnnouncementSerializer
- GET /hr/tl/announcements/ — list TL announcements

## Team lead listing
- GET /hr/tl/list/ — Permissions: IsAuthenticated (or IsHROrManagement if restricted)

## Attendance (HR views)
- GET /hr/attendance/?month=YYYY-MM — list of attendances across org (HROrManagement)

## Leave management (HR)
- GET /hr/leave/ — list all leaves (HROrManagement)
- HR approval endpoints use IsHROrManagement

## Other HR admin endpoints
- Employee listing, profile updates, etc. — standard CRUD protected by IsHROrManagement

---
# TL APP

Base: `/tl/`

## Announcement (TL)
- POST /tl/announcement/create/ — Permissions: IsTL
  Request: TLAnnouncementSerializer (title, body, date, audience)
- GET /tl/announcement/list/ — list TL announcements visible to TL

## Team members & attendance
- GET /tl/team/members/ — list team members for TL (IsTL)
- GET /tl/team/attendance/?month=YYYY-MM — attendance for TL's team
- GET /tl/dashboard/ — aggregated metrics for TL's team

## Leave actions for TL
- GET /tl/leave/pending/ — list pending leaves for TL's team
- POST /tl/leave/{leave_id}/action/ — approve/reject by TL

---
# Models & Common Schemas (summary)

## EmployeeProfile (partial)
- user: FK to User
- emp_id, work_email, username, first_name, last_name, profile_photo, team_lead, role, is_active

## Attendance
- user, date, clock_in, clock_out, duration_time, duration_seconds, status

## LeaveRequest
- profile, leave_type, start_date, end_date, days, status, tl, hr, tl_remarks, hr_remarks

## Notification
- to_user, title, body, notif_type, is_read, extra

## TimesheetEntry
- profile, date, task, start_time, end_time, duration_seconds

---
# Error handling & status codes
- 200 OK for successful GETs
- 201 Created for successful resource creation
- 400 Bad Request for validation errors
- 401 Unauthorized for missing/invalid token
- 403 Forbidden for insufficient permissions
- 404 Not Found for missing resources
- 500 Internal Server Error for unexpected conditions

---
# Examples & Notes
- All multipart employee creation endpoints accept nested JSON strings or files using keys like `contact.first_name` or `job.id_image`.
- Protected media endpoint: `/emp/protected-media/{profile_pk}/{field_name}/` returns FileResponse for allowed fields (profile_photo, aadhaar_image, pan_image, passport_image, id_image) when owner or HR/Management requests it.

---
# Contact & Contributions
If you need the Postman collection or an OpenAPI JSON/YAML, or unit tests autogenerated, I can produce them next.
