from django.contrib import admin
from .models import Client, DeliveryManager, Project
from .models import ModuleProgress, RiskAlert

admin.site.register(ModuleProgress)
admin.site.register(RiskAlert)
admin.site.register(Client)
admin.site.register(DeliveryManager)
admin.site.register(Project)