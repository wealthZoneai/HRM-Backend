from django.db import transaction
from .models import EmployeeIDSequence

EMP_ID_PREFIX = "WZG-AI"
EMP_ID_WIDTH = 4


@transaction.atomic
def generate_emp_id():
    seq, _ = EmployeeIDSequence.objects.select_for_update().get_or_create(id=1)
    seq.last_value += 1
    seq.save(update_fields=["last_value"])

    return f"{EMP_ID_PREFIX}-{seq.last_value:0{EMP_ID_WIDTH}d}"
