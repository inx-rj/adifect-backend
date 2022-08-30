from django.contrib import admin

# Register your models here.
from .models import WorkFlowLevels, Stages, WorkFlow

admin.site.register(WorkFlowLevels)

admin.site.register(WorkFlow)

admin.site.register(Stages)