from email.policy import default
from django.db import models
from autoslug import AutoSlugField
from authentication.models import CustomUser
import os
from authentication.manager import SoftDeleteManager
from django.db.models import CharField
from django.db.models import Q
from django.db import IntegrityError
from django.core.exceptions import ValidationError
import datetime as dt
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
from PIL import Image
import sys
# from administrator.models import Skills

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


class Industry(BaseModel):
    industry_name = models.CharField(max_length=50)
    slug = AutoSlugField(populate_from='industry_name')
    description = models.TextField(default=None, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Industry'

    def clean(self):
        exist_company = Industry.objects.filter(industry_name=self.industry_name, is_trashed=False)
        if self.id:
            exist_company = exist_company.exclude(pk=self.id)
        if exist_company:
            raise ValidationError("Industry Already Exist")

    def __str__(self) -> CharField:
        return self.industry_name


class Company(BaseModel):
    class Type(models.IntegerChoices):
        person = 0
        agency = 1

    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200, null=True, blank=True)
    company_type = models.IntegerField(choices=Type.choices, default=Type.agency)
    agency = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='company_agency', blank=True,
                               null=True)
    is_active = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Company'

    def clean(self):
        exist_company = Company.objects.filter(name__iexact=self.name, agency=self.agency, is_trashed=False)
        if self.id:
            exist_company = exist_company.exclude(pk=self.id)
        if exist_company:
            raise ValidationError("Company Already Exist")

    def __str__(self) -> CharField:
        return self.name


class WorksFlow(BaseModel):
    name = models.CharField(max_length=200, null=False, blank=False)
    agency = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='workflow_agency', blank=True,
                               null=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, related_name='workflow_company', blank=True,
                                null=True)
    is_active = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'WorksFlow'

    def clean(self):
        exist_WorksFlow = WorksFlow.objects.filter(name__iexact=self.name,agency=self.agency,is_trashed=False)
        if self.id:
            exist_WorksFlow = exist_WorksFlow.exclude(pk=self.id)
        if exist_WorksFlow:
            raise ValidationError("Works Flow With This Name Already Exist")

    def __str__(self):
        return self.name



class AgencyLevel(BaseModel):
    class Agency_Levels(models.IntegerChoices):
        Agency_admin = 1
        Agency_Marketer = 2
        Agency_Approver = 3

    user = models.ForeignKey(CustomUser,related_name='agency_level',on_delete=models.SET_NULL, null=True, blank=True)
    levels = models.IntegerField(choices=Agency_Levels.choices, default=None)
    is_active = models.BooleanField(default=True)

        


class InviteMember(BaseModel):
    class Status(models.IntegerChoices):
        SEND = 0
        ACCEPT = 1
        REJECT = 2

    agency = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='invite_member_agency', blank=True,
                               null=True)
    user = models.ForeignKey(AgencyLevel, on_delete=models.SET_NULL, related_name='invite_member_user', null=True,
                             blank=True)
    status = models.IntegerField(choices=Status.choices, default=Status.SEND)
    email = models.EmailField(max_length=254,default=None,null=True,blank=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, related_name='invite_company_list', null=True,
                                blank=True)
    is_blocked = models.BooleanField(default=False)                            
    class Meta:
        verbose_name_plural = 'Invite Members'

    def __str__(self):
        return self.get_status_display()


class Workflow_Stages(BaseModel):
    name = models.CharField(max_length=200, null=False, blank=False)
    is_approval = models.BooleanField(default=False)
    is_all_approval = models.BooleanField(default=False)
    approvals = models.ManyToManyField(InviteMember, related_name="stage_approvals")
    is_observer = models.BooleanField(default=False)
    observer = models.ManyToManyField(InviteMember, related_name="stage_observer")
    workflow = models.ForeignKey(WorksFlow,  related_name="stage_workflow",on_delete=models.SET_NULL, null=True,
                                 blank=True)
    order = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Workflow Stages'

    def __str__(self):
        return self.name


class DAM(BaseModel):
    class Type(models.IntegerChoices):
        FOLDER = 1
        COLLECTION = 2
        IMAGE = 3
    name = models.CharField(max_length=5000, default=None,null=True, blank=True)
    agency = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="dam_agency")
    type = models.IntegerField(choices=Type.choices, default=None)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)
    is_favourite = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'DAM'

def fileLocation(instance, dam_media):
    if instance.dam.type == 1:
        return 'dam_media/{0}/{1}'.format(instance.dam.agency.username, os.path.basename(dam_media))
    if instance.dam.type == 2:
        return 'dam_media/{0}/{1}'.format(instance.dam.agency.username + 'collections/',
                                          os.path.basename(dam_media))
    if instance.dam.type == 3:
        return 'dam_media/{0}/{1}'.format(instance.dam.agency.username + 'images/',
                                          os.path.basename(dam_media))


class DamMedia(BaseModel):
    class Type(models.IntegerChoices):
        Public = 1
        Private = 0
    dam = models.ForeignKey(DAM, on_delete=models.CASCADE, null=True, blank=True, related_name="dam_media")
    media = models.FileField(upload_to=fileLocation, blank=True, null=True)
    thumbnail = models.FileField(upload_to=fileLocation, null=True, blank=True)
    is_video = models.BooleanField(default=False)
    title = models.CharField(max_length=5000, default=None,null=True, blank=True)
    description = models.CharField(max_length=5000, default=None,null=True, blank=True)
    image_favourite = models.BooleanField(default=False)
    limit_usage_toggle = models.BooleanField(default=False)
    limit_usage = models.IntegerField(default=None,null=True,blank=True)
    limit_used = models.IntegerField(default=0)
    usage = models.IntegerField(choices=Type.choices,null=True,blank=True, default=None)
    usage_limit_reached = models.BooleanField(default=False)
    skills = models.ManyToManyField('administrator.skills',blank=True)
    tags = models.CharField(max_length=10000,null=True, blank=True)


    class Meta:
        verbose_name_plural = 'DAM Media'
    
    def save(self, **kwargs):
        
        if str(self.media).endswith(".mp4"):
            self.thumbnail=self.media
            self.is_video= True
            super(DamMedia, self).save()
        else:
            output_size = (250, 250)
            output_thumb = BytesIO()

            img = Image.open(self.media)
            img_name = self.media.name.split('.')[0]

            img.thumbnail(output_size)
            img.save(output_thumb,format=img.format,quality=90)

            self.thumbnail = InMemoryUploadedFile(output_thumb, 'ImageField', f"{img_name}_thumb.jpg", 'image/jpeg', sys.getsizeof(output_thumb), None)

            super(DamMedia, self).save()




# -------------------------------------- testing -----------------------------------------#
class TestModal(models.Model):
    class Status(models.IntegerChoices):
        SEND = 0
        ACCEPT = 1
        REJECT = 2

    name = models.CharField(max_length=50, default=None)
    description = models.CharField(max_length=200, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    status = models.IntegerField(choices=Status.choices, default=Status.SEND)
    media = models.FileField(upload_to='test_media', blank=True, null=True)
