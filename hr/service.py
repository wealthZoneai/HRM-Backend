from django.utils.dateparse import parse_datetime
from django.db.models import Q

class AttendanceCorrectionService:

    @staticmethod
    def correct_attendance(attendance, data):
        """
        Business rules for HR attendance correction
        """

        clock_in_str = data.get("clock_in")
        clock_out_str = data.get("clock_out")
        status = data.get("status")
        note = data.get("note", "Corrected by HR")

        # ---------------- Clock-in correction ----------------
        if clock_in_str:
            clock_in = parse_datetime(clock_in_str)
            if clock_in:
                new_date = clock_in.date()

                # Rule: Same user cannot have 2 records on same date
                conflict_exists = attendance.__class__.objects.filter(
                    user=attendance.user,
                    date=new_date
                ).exclude(id=attendance.id).exists()

                if not conflict_exists:
                    attendance.date = new_date

                attendance.clock_in = clock_in

        # ---------------- Clock-out correction ----------------
        if clock_out_str:
            clock_out = parse_datetime(clock_out_str)
            if clock_out:
                attendance.clock_out = clock_out

        # ---------------- Status correction ----------------
        if status:
            attendance.status = status

        # ---------------- HR note handling ----------------
        hr_note = f"HR correction: {note}"

        if not attendance.note:
            attendance.note = hr_note
        elif hr_note not in attendance.note:
            attendance.note += f"\n{hr_note}"

        # ---------------- Flags ----------------
        attendance.manual_entry = True
        attendance.save()

        return attendance
