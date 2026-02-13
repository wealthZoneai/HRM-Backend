# emp/constants.py

LEAVE_TYPE_CHOICES = [
    ("CASUAL", "Casual Leave"),
    ("SICK", "Sick Leave"),
    ("PAID", "Paid Leave"),
    ("UNPAID", "Unpaid Leave"),
    ("MATERNITY", "Maternity Leave"),
    ("PATERNITY", "Paternity Leave"),
]

# IMPORTANT:
# First value = DB-safe constant
# Second value = human readable label
EMPLOYEE_DEPARTMENT_CHOICES = [
    ("PYTHON", "Python"),
    ("QA", "QA"),
    ("JAVA", "Java"),
    ("UIUX", "UI/UX"),
    ("REACT", "React"),
    ("CYBER_SECURITY", "Cyber Security"),
    ("DIGITAL_MARKETING", "Digital Marketing"),
    ("HR", "HR"),
    ("BDM", "BDM"),
    ("NETWORKING", "Networking"),
    ("CLOUD", "Cloud"),
]
