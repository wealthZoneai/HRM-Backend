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
    ("Python", "Python"),
    ("QA", "QA"),
    ("Java", "Java"),
    ("UI/UX", "UI/UX"),
    ("React", "React"),
    ("Cyber Security", "Cyber Security"),
    ("Digital Marketing", "Digital Marketing"),
    ("HR", "HR"),
    ("BDM", "BDM"),
    ("Networking", "Networking"),
    ("Cloud", "Cloud"),
]
