from django.contrib import admin

# Register your models here.
from .models import WorksFlow, Workflow_Stages, InviteMember, Industry, Company

admin.site.register(Industry)
admin.site.register(Company)
admin.site.register(Workflow_Stages)

admin.site.register(InviteMember)



@admin.register(WorksFlow)
class WorksFlowAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super(WorksFlowAdmin, self).get_queryset(request)
        return qs.filter(is_trashed=False)
