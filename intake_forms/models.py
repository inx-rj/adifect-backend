from django.db import models
from django.utils.text import slugify

from authentication.models import CustomUser
from common.models import BaseModel
import uuid


class IntakeForm(BaseModel):
    uuid = models.UUIDField(editable=False, default=uuid.uuid4, unique=True)
    form_slug = models.CharField(null=True, blank=True, max_length=50)
    title = models.CharField(max_length=200, unique=True)

    class Meta:
        verbose_name_plural = 'IntakeForms'

    def save(self, *args, **kwargs):
        self.execute_custom_method()

        super().save(*args, **kwargs)

    @classmethod
    def create(cls, *args, **kwargs):
        instance = cls(*args, **kwargs)
        instance.execute_custom_method()

        instance.save()
        return instance

    def execute_custom_method(self):
        self.form_slug = slugify(self.title)

    def __str__(self):
        return f'{self.id} - {self.title} - {self.form_slug}'


class IntakeFormFieldVersion(BaseModel):
    uuid = models.UUIDField(editable=False, default=uuid.uuid4, unique=True)
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
    uuid = models.UUIDField(editable=False, default=uuid.uuid4, unique=True)
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
    uuid = models.UUIDField(editable=False, default=uuid.uuid4, unique=True)
    form_version = models.ForeignKey(IntakeFormFieldVersion, related_name='intake_form_submission_form_version',
                                     on_delete=models.SET_NULL, null=True, blank=True)
    submitted_user = models.ForeignKey(CustomUser, related_name='intake_form_submission_user',
                                       on_delete=models.SET_NULL, null=True, blank=True)
    submission_data = models.JSONField()

    class Meta:
        verbose_name_plural = 'IntakeFormSubmissions'

    def __str__(self):
        return f'{self.id}'


class FormTask(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    form_submission = models.ForeignKey(IntakeFormSubmissions, related_name='form_map_submission',
                                        on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'FormTasks'

    def __str__(self):
        return f'{self.id}--{self.name}--{self.form_submission_id}'

class FormTaskMapping(BaseModel):
    form_task = models.ForeignKey(FormTask, related_name='form_map_task',
                                           on_delete=models.SET_NULL, null=True, blank=True)
    assign_to = models.ForeignKey(CustomUser, related_name='form_map_assign_to',
                                  on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'FormTaskMappings'

    def __str__(self):
        return f'{self.id}--{self.form_task_id}--{self.assign_to_id}'