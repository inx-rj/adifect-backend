from django.contrib import admin

from intake_forms.models import IntakeForm, IntakeFormFields, IntakeFormSubmissions, IntakeFormFieldVersion

admin.site.register(IntakeForm)
admin.site.register(IntakeFormFields)
admin.site.register(IntakeFormSubmissions)
admin.site.register(IntakeFormFieldVersion)