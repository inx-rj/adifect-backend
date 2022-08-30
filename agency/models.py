from django.db import models
from autoslug import AutoSlugField
from authentication.models import CustomUser

from administrator.models import Job

# Create your models here.

class BaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True

        
class Stages(BaseModel):
    agency = models.ForeignKey(CustomUser,on_delete=models.CASCADE, related_name="agency_stage", default=None)
    stage_name=models.CharField(max_length=50)
    slug = AutoSlugField(populate_from='stage_name')
    description = models.TextField(default=None,blank=True,null=True)
    is_active = models.BooleanField(default=True)
   
    def __str__(self) -> str:
        return self.stage_name



class WorkFlowLevels(BaseModel):
    agency = models.ForeignKey(CustomUser,on_delete=models.CASCADE, related_name="agency_level", default=None)
    level_name=models.CharField(max_length=50,default=None)
    slug = AutoSlugField(populate_from='level_name')
    description = models.TextField(default=None,blank=True,null=True)
    is_active = models.BooleanField(default=True)
    def __str__(self) -> str:
        return self.level_name

class WorkFlow(models.Model):
    agency = models.ForeignKey(CustomUser,on_delete=models.CASCADE, related_name="agency", default=None)
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE, related_name="user", default=None)
    stage = models.ForeignKey(Stages,on_delete=models.CASCADE,default=None)
    level = models.ForeignKey(WorkFlowLevels,on_delete=models.CASCADE,default=None)


class InviteMember(BaseModel):
    class Status(models.IntegerChoices):
        SEND = 0
        ACCEPT = 1
        REJECT = 2
    agency = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='invite_member_agency', default=None)
    user = models. ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='invite_member_user',null=True,blank=True, default=None)
    status = models.IntegerField(choices=Status.choices, default=Status.SEND)

    class Meta:
        verbose_name = 'InviteMember'
        verbose_name_plural = 'InviteMembers'

    def __str__(self):
        return self.agency



