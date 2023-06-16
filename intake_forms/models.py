from django.db import models

from authentication.models import CustomUser
from common.models import BaseModel


class IntakeForm(BaseModel):
    title = models.CharField(max_length=200)

    class Meta:
        verbose_name_plural = 'IntakeForms'

    def __str__(self):
        return f'{self.id} - {self.title}'


class IntakeFormFieldVersion(BaseModel):
    intake_form = models.ForeignKey(IntakeForm, related_name='intake_form_field_version_form',
                                    on_delete=models.SET_NULL, null=True, blank=True)
    version = models.FloatField()
    user = models.ForeignKey(CustomUser, related_name='intake_form_field_version_user', on_delete=models.SET_NULL,
                             null=True, blank=True)

    class Meta:
        verbose_name_plural = 'IntakeFormVersion'

    def __str__(self):
        return f'{self.id}'


class IntakeFormFields(BaseModel):
    form_version = models.ForeignKey(IntakeFormFieldVersion, related_name='intake_form_fields_form_version',
                                     on_delete=models.SET_NULL, null=True, blank=True)
    field_name = models.CharField(max_length=200)
    field_type = models.CharField(max_length=50)
    options = models.JSONField(null=True, blank=True)
    meta_data = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'IntakeFormFields'

    def __str__(self):
        return f'{self.id}'


class IntakeFormSubmissions(BaseModel):
    form_version = models.ForeignKey(IntakeFormFieldVersion, related_name='intake_form_submission_form_version',
                                     on_delete=models.SET_NULL, null=True, blank=True)
    submitted_user = models.ForeignKey(CustomUser, related_name='intake_form_submission_user',
                                       on_delete=models.SET_NULL, null=True, blank=True)
    submission_data = models.JSONField()

    class Meta:
        verbose_name_plural = 'IntakeFormSubmissions'

    def __str__(self):
        return f'{self.id}'
