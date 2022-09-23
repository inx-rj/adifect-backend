from django.contrib import admin

# Register your models here.
from .models import WorksFlow, Workflow_Stages, InviteMember, Industry, Company, NewModel_latest

admin.site.register(Industry)
admin.site.register(Company)
admin.site.register(Workflow_Stages)

admin.site.register(InviteMember)
admin.site.register(NewModel_latest)



@admin.register(WorksFlow)
class WorksFlowAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super(WorksFlowAdmin, self).get_queryset(request)
        return qs.filter(is_trashed=False)
