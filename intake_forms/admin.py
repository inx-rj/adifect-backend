from django.contrib import admin

from intake_forms.models import IntakeForm, IntakeFormFields, IntakeFormSubmissions, IntakeFormFieldVersion, FormTask, \
    FormTaskMapping

admin.site.register(IntakeForm)
admin.site.register(IntakeFormFields)
admin.site.register(IntakeFormSubmissions)
admin.site.register(IntakeFormFieldVersion)
admin.site.register(FormTask)
admin.site.register(FormTaskMapping)
