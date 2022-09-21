from email import message
import os
from operator import truediv
from pyexpat import model

from django.db.models import CharField
from typing_extensions import Required
from django.db import models
from autoslug import AutoSlugField
from authentication.models import CustomUser
from django.core.exceptions import ValidationError
from authentication.manager import SoftDeleteManager
from agency.models import WorksFlow, Company, Industry


def validate_attachment(value):
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    ext = ext.strip()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.doc', '.docx', '.mp4', '.pdf', '.xlsx', '.csv']
    if not ext.lower() in valid_extensions:
        raise ValidationError("Unsupported file extension....")
    return value


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


class Category(BaseModel):
    category_name = models.CharField(max_length=50)
    slug = AutoSlugField(populate_from='category_name')
    description = models.TextField(default=None, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.category_name

    class Meta:
        verbose_name_plural = 'Category'


# ---------------------------------- old ---------------------------------------------#
'''
class Industry(BaseModel):
    industry_name = models.CharField(max_length=50)
    slug = AutoSlugField(populate_from='industry_name')
    description = models.TextField(default=None, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.industry_name

    class Meta:
        verbose_name_plural = 'Industry'
'''


# ---------------------------------- end ------------------------------------------------#

class Level(BaseModel):
    level_name = models.CharField(max_length=50)
    slug = AutoSlugField(populate_from='level_name')
    description = models.TextField(default=None, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.level_name

    class Meta:
        verbose_name_plural = 'Level'


class Skills(BaseModel):
    skill_name = models.CharField(max_length=50, unique=True)
    slug = AutoSlugField(populate_from='skill_name')
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.skill_name

    class Meta:
        verbose_name_plural = 'Skills'


# ---------------------- --------- old ---------------------------------------------#
'''
class Company(BaseModel):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    company_type = models.CharField(choices=(('0', 'person'), ('1', 'agency')), max_length=30, default='1')
    is_active = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Company'

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name_plural = 'Company'
'''
# ---------------------------------- end ------------------------------------------------#


jobType = (('0', 'Fixed'), ('1', 'Hourly'))


class Job(BaseModel):
    class Status(models.IntegerChoices):
        Draft = 0
        Template = 1
        Post = 2

    title = models.CharField(max_length=250)
    description = models.TextField(default=None, blank=True, null=True)
    job_type = models.CharField(choices=jobType, max_length=30, default='0')
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True, blank=True)
    expected_delivery_date = models.DateField(default=None)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    tags = models.CharField(max_length=10000)
    skills = models.ManyToManyField(Skills)
    image_url = models.CharField(default=None, max_length=50000, blank=True, null=True)
    sample_work_url = models.CharField(default=None, max_length=50000, blank=True, null=True)
    related_jobs = models.ManyToManyField('self', blank=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, related_name="job_company", null=True, blank=True)
    industry = models.ForeignKey(Industry, on_delete=models.SET_NULL, related_name="job_industry", null=True,
                                 blank=True)
    workflow = models.ForeignKey(WorksFlow, on_delete=models.SET_NULL, related_name="job_workflow", blank=True,
                                 null=True)
    job_due_date = models.DateField(auto_now_add=True)
    due_date_index = models.IntegerField(null=True,blank=True,default=0)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    template_name = models.CharField(max_length=250, null=True, blank=True)
    status = models.IntegerField(choices=Status.choices, default=Status.Post)


    class Meta:
        verbose_name_plural = 'Job'

    def clean(self):
        exist_job = Job.objects.filter(template_name=self.template_name, is_trashed=False)
        if self.id:
            exist_job = exist_job.exclude(pk=self.id)
        if exist_job:
            raise ValidationError("Job Template With This Name Already Exist")

    def __str__(self) -> str:
        return f'{self.title}'



class JobAttachments(BaseModel):
    job = models.ForeignKey(Job, related_name="images", on_delete=models.SET_NULL, null=True, blank=True)
    job_images = models.FileField(upload_to='job_images', blank=True, null=True)
    work_sample_images = models.FileField(upload_to='work_sample_images', blank=True, null=True)

    # def delete(self, *args, **kwargs):
    #     if self.job_images:
    #         self.job_images.delete()
    #     if self.work_sample_images:
    #         self.work_sample_images.delete()
    #
    #     super().delete(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.job}'

    class Meta:
        verbose_name_plural = 'Job Attachments'


class JobApplied(BaseModel):
    class Status(models.IntegerChoices):
        APPLIED = 0
        IN_REVIEW = 1
        HIRE = 2

    # cover_letter = models.TextField()
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True)
    job_bid_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # duration = models.CharField(max_length=200, default=None, null=True, blank=True)
    links = models.CharField(default=None, max_length=50000, blank=True, null=True)
    offer_price = models.DecimalField(default=None, max_digits=10, decimal_places=2, blank=True, null=True)
    due_date = models.DateField(default=None, blank=True, null=True)
    proposed_price = models.DecimalField(default=None, max_digits=10, decimal_places=2, blank=True, null=True)
    proposed_due_date = models.DateField(default=None, blank=True, null=True)
    status = models.IntegerField(choices=Status.choices, default=Status.APPLIED)
    job_applied_date = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Jobs Applied'


class JobAppliedAttachments(BaseModel):
    job_applied = models.ForeignKey(JobApplied, related_name="images", on_delete=models.SET_NULL, null=True, blank=True)
    job_applied_attachments = models.FileField(upload_to='job_applied_attachments', blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Job Applied Attachments'


class JobHired(BaseModel):
    user = models.ManyToManyField(CustomUser)
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True)
    hire_date = models.DateField(auto_now_add=True)
    status = models.CharField(choices=(('0', 'In progress'), ('1', 'In Review'), ('2', 'Completed'), ('3', 'Closed')),
                              max_length=30, default='0')

    class Meta:
        verbose_name_plural = 'Jobs Hired'


class Activities(BaseModel):
    job_id = models.ForeignKey(Job, on_delete=models.SET_NULL, related_name="job_id", db_column='job_id', null=True,
                               blank=True)
    hired_user = models.ForeignKey(JobHired, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.CharField(max_length=100, default=None, blank=True, null=True)
    date_time = models.DateTimeField(auto_now_add=True, editable=False)
    activity_type = models.CharField(choices=(('0', 'Chat'), ('1', 'Follow Up Request'), ('2', 'Rating')),
                                     max_length=30, default='0')
    sender = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="sender_id")

    class Meta:
        verbose_name_plural = 'Activities'


class ActivityAttachments(BaseModel):
    activities = models.ForeignKey(Activities, related_name="images", on_delete=models.SET_NULL, null=True, blank=True)
    activity_attachments = models.FileField(upload_to='activity_attachments', blank=True, null=True,
                                            validators=[validate_attachment])
    class Meta:
        verbose_name_plural = 'Activity Attachments'


class PreferredLanguage(BaseModel):
    class Proficiency(models.IntegerChoices):
        BASIC = 0
        INTERMEDIATE = 1
        FLUENT = 2

    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    ln_code = models.CharField(max_length=100, null=False, blank=False)
    ln_proficiency = models.IntegerField(choices=Proficiency.choices, default=Proficiency.BASIC)

    class Meta:
        verbose_name_plural = 'Preferred Languages'

    def __str__(self):
        return self.ln_code


class JobTasks(BaseModel):
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True, related_name="jobtasks_job")
    title = models.CharField(max_length=3000, null=False, blank=False)
    due_date = models.DateField(auto_now_add=False)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> CharField:
        return self.title

    class Meta:
        verbose_name_plural = 'Job Task'


class JobTemplate(BaseModel):
    class JobType(models.IntegerChoices):
        Fixed = 0
        Hourly = 1

    class Status(models.IntegerChoices):
        Draft = 0
        Template = 1
        Post = 2

    template_name = models.CharField(max_length=250)
    title = models.CharField(max_length=250)
    description = models.TextField(default=None, blank=True, null=True)
    job_type = models.IntegerField(choices=JobType.choices, default=JobType.Fixed)
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, related_name="jobtemplate_level", null=True, blank=True)
    expected_delivery_date = models.DateField(default=None)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    tags = models.CharField(max_length=10000)
    skills = models.ManyToManyField(Skills)
    image_url = models.CharField(default=None, max_length=50000, blank=True, null=True)
    sample_work_url = models.CharField(default=None, max_length=50000, blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, related_name="jobtemplate_company", null=True,
                                blank=True)
    industry = models.ForeignKey(Industry, on_delete=models.SET_NULL, related_name="jobtemplate_industry", null=True,
                                 blank=True)
    workflow = models.ForeignKey(WorksFlow, on_delete=models.SET_NULL, related_name="jobtemplate_workflow", blank=True,
                                 null=True)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name="jobtemplate_user", null=True,
                             blank=True)
    status = models.IntegerField(choices=Status.choices, default=Status.Template)


    class Meta:
        verbose_name_plural = 'Job Template'

    def clean(self):
        exist_job = JobTemplate.objects.filter(template_name=self.template_name, is_trashed=False)
        if self.id:
            exist_job = exist_job.exclude(pk=self.id)
        if exist_job:
            raise ValidationError("Job Template With This Name Already Exist")

    def __str__(self) -> str:
        return f'{self.template_name}'

def file_generate_upload_path(instance, filename):
	# Both filename and instance.file_name should have the same values
    return f"files/{instance.job_template.template_name}"



class JobTemplateAttachments(BaseModel):
    job_template = models.ForeignKey(JobTemplate, related_name="job_template_images", on_delete=models.SET_NULL,
                                     null=True, blank=True)
    job_template_images = models.FileField(upload_to=file_generate_upload_path, blank=True, null=True)
    work_sample_images = models.FileField(upload_to=file_generate_upload_path, blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Job Template Attachments'
