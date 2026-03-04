# emp/constants.py

LEAVE_TYPE_CHOICES = [
    ("CASUAL", "Casual_Leave"),
    ("SICK", "Sick_Leave"),
    ("PAID", "Paid_Leave"),
    ("UNPAID", "Unpaid_Leave"),
    ("MATERNITY", "Maternity_Leave"),
    ("PATERNITY", "Paternity_Leave"),
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
