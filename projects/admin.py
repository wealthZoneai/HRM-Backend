from django.contrib import admin
from .models import Project, ProjectModule, Task, SubTask

admin.site.register(Project)
admin.site.register(ProjectModule)
admin.site.register(Task)
admin.site.register(SubTask)
