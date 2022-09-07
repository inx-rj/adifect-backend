from django.db import models
from autoslug import AutoSlugField
from authentication.models import CustomUser

from administrator.models import Job
from authentication.manager import SoftDeleteManager


# Create your models here.

class BaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)
    is_trashed = models.BooleanField(default=False)
    objects = SoftDeleteManager()
    objects_with_deleted = SoftDeleteManager(deleted=True)

    def delete(self, *args, **kwargs):
        self.is_trashed = True
        self.save()

    def restore(self):
        self.is_trashed = False
        self.save()

    class Meta:
        abstract = True


class WorksFlow(BaseModel):
    name = models.CharField(max_length=200, null=False, blank=False)
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, related_name="workflow_job", blank=True, null=True)
    agency = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='workflow_agency', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'WorksFlow'

    def __str__(self):
        return self.name


class InviteMember(BaseModel):
    class Status(models.IntegerChoices):
        SEND = 0
        ACCEPT = 1
        REJECT = 2

    agency = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='invite_member_agency',blank=True, null=True)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='invite_member_user', null=True,
                             blank=True)
    status = models.IntegerField(choices=Status.choices, default=Status.SEND)

    class Meta:
        verbose_name_plural = 'Invite Members'

    def __str__(self):
        return self.agency.first_name


class Workflow_Stages(BaseModel):
    name = models.CharField(max_length=200, null=False, blank=False)
    is_approval = models.BooleanField(default=False)
    approvals = models.ManyToManyField(InviteMember, related_name="stage_approvals")
    is_observer = models.BooleanField(default=False)
    observer = models.ManyToManyField(InviteMember, related_name="stage_observer")
    workflow = models.ForeignKey(WorksFlow, on_delete=models.SET_NULL, related_name="stage_workflow",null=True, blank=True)
    order = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Workflow Stages'

    def __str__(self):
        return self.name
