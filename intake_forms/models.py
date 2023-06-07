from django.db import models

from authentication.models import CustomUser
from common.models import BaseModel


class   IntakeForm(BaseModel):
    title = models.CharField(max_length=200, unique=True)

    class Meta:
        verbose_name_plural = 'IntakeForms'

    def __str__(self):
        return f'{self.id} - {self.title}'


class IntakeFormFields(BaseModel):
    intake_form = models.ForeignKey(IntakeForm, related_name='field_intake_form', on_delete=models.SET_NULL, null=True,
                                    blank=True)
    field_name = models.CharField(max_length=200)
    field_type = models.CharField(max_length=50)
    options = models.JSONField(null=True, blank=True)
    version = models.FloatField()

    class Meta:
        verbose_name_plural = 'IntakeFormFields'

    def __str__(self):
        return self.id


class IntakeFormSubmissions(BaseModel):
    intake_form = models.ForeignKey(IntakeForm, related_name='submission_intake_form', on_delete=models.SET_NULL,
                                    null=True, blank=True)
    user = models.ForeignKey(CustomUser, related_name='intake_form_submission_user', on_delete=models.SET_NULL,
                             null=True, blank=True)
    submission_data = models.JSONField()
    version = models.FloatField()

    class Meta:
        verbose_name_plural = 'IntakeFormSubmissions'

    def __str__(self):
        return self.id
