from email import message
import os
from operator import truediv
from pyexpat import model
from typing_extensions import Required
from django.db import models
from autoslug import AutoSlugField
from authentication.models import CustomUser
from django.core.exceptions import ValidationError


def validate_attachment(value):
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    ext = ext.strip()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.doc', '.docx', '.mp4', '.pdf', '.xlsx','.csv']
    if not ext.lower() in valid_extensions:
        raise ValidationError("Unsupported file extension....")
    return value

class BaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True

class Category(BaseModel):
    category_name=models.CharField(max_length=50)
    slug = AutoSlugField(populate_from='category_name')
    description = models.TextField(default=None,blank=True,null=True)
    is_active = models.BooleanField(default=True)
   
    def __str__(self) -> str:
        return self.category_name


class Industry(BaseModel):
    industry_name=models.CharField(max_length=50)
    slug = AutoSlugField(populate_from='industry_name')
    description = models.TextField(default=None,blank=True,null=True)
    is_active = models.BooleanField(default=True)
        
    def __str__(self) -> str:
        return self.industry_name


class Level(BaseModel):
    level_name=models.CharField(max_length=50)
    slug = AutoSlugField(populate_from='level_name')
    description = models.TextField(default=None,blank=True,null=True)
    is_active = models.BooleanField(default=True)
        
    def __str__(self) -> str:
        return self.level_name


class Skills(BaseModel):
    skill_name=models.CharField(max_length=50, unique=True) 
    slug = AutoSlugField(populate_from='skill_name')
    is_active = models.BooleanField(default=True)
            
    def __str__(self) -> str:
        return self.skill_name


class Company(BaseModel):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    company_type = models.CharField(choices=(('0', 'person'), ('1', 'agency')), max_length=30, default='1')
    is_active = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Company' 

    def __str__(self) -> str:
        return self.name


jobType = (('0', 'Fixed'), ('1', 'Hourly'))

class Job(BaseModel):
    title =  models.CharField(max_length=250)
    description = models.TextField(default=None,blank=True,null=True)
    job_type = models.CharField(choices=jobType, max_length=30, default='0')
    category = models.ForeignKey(Category,on_delete=models.CASCADE, blank=True, null=True)
    industry = models.ForeignKey(Industry,on_delete=models.CASCADE, blank=True, null=True)
    level = models.ForeignKey(Level,on_delete=models.CASCADE, blank=True, null=True)    
    expected_delivery_date = models.DateField(default=None)
    price = models.DecimalField(max_digits=10,decimal_places=2)
    tags = models.CharField(max_length=10000)
    skills = models.ManyToManyField(Skills)
    image_url = models.CharField(default=None,max_length=50000,blank=True,null=True)
    sample_work_url = models.CharField(default=None, max_length=50000, blank=True, null=True)
    related_jobs = models.ManyToManyField('self', blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, blank=True, null=True)
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    status = models.PositiveSmallIntegerField(default=0)
  
    def __str__(self) -> str:
        return f'{self.title}' 



class JobAttachments(models.Model):
    job = models.ForeignKey(Job,related_name="images",on_delete=models.CASCADE)
    job_images = models.FileField(upload_to='job_images', blank=True,null=True)
    work_sample_images = models.FileField(upload_to='work_sample_images', blank=True,null=True)


    def delete(self, *args, **kwargs):
        if self.job_images:
            self.job_images.delete()
        if self.work_sample_images:
           self.work_sample_images.delete()
        
        super().delete(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.job.title}' 


class JobApplied(models.Model):

    class Status(models.IntegerChoices):
        APPLIED = 0
        IN_REVIEW = 1
        HIRE = 2

    cover_letter = models.TextField()
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    job = models.ForeignKey(Job,on_delete=models.CASCADE)
    job_bid_price = models.DecimalField(max_digits=10,decimal_places=2, null=True, blank=True)
    duration = models.CharField(max_length=200,default=None,null=True,blank=True)
    links = models.CharField(default=None,max_length=50000,blank=True,null=True)
    offer_price = models.DecimalField(default=None,max_digits=10,decimal_places=2,blank=True,null=True)
    due_date = models.DateField(default=None,blank=True,null=True)
    proposed_price = models.DecimalField(default=None,max_digits=10,decimal_places=2,blank=True,null=True)
    proposed_due_date = models.DateField(default=None,blank=True,null=True)
    status = models.IntegerField(choices=Status.choices, default=Status.APPLIED)
    job_applied_date = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = 'Jobs Applied'  


class JobAppliedAttachments(models.Model):
    job_applied = models.ForeignKey(JobApplied,related_name="images",on_delete=models.CASCADE)
    job_applied_attachments = models.FileField(upload_to='job_applied_attachments', blank=True,null=True)


class JobHired(models.Model):
    user = models.ManyToManyField(CustomUser)
    job = models.ForeignKey(Job,on_delete=models.CASCADE)
    hire_date = models.DateField(auto_now_add=True)
    status = models.CharField(choices=(('0', 'In progress'), ('1', 'In Review'), ('2', 'Completed'), ('3', 'Closed')), max_length=30, default='0')

    class Meta:
        verbose_name = 'Jobs Hired' 

class Activities(models.Model):
    job_owner = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name="job_owner_id", default=None)
    hired_user = models.ForeignKey(JobHired, on_delete=models.CASCADE, default=None)
    message = models.CharField(max_length=100,default=None,blank=True,null=True)
    date_time = models.DateTimeField(auto_now_add=True, editable=False)
    activity_type = models.CharField(choices=(('0', 'Chat'), ('1', 'Follow Up Request'), ('2','Rating')), max_length=30, default='0')
    sender = models.ForeignKey(CustomUser,on_delete=models.CASCADE, related_name="sender_id", default=None)


class ActivityAttachments(models.Model):
    activities = models.ForeignKey(Activities,related_name="images",on_delete=models.CASCADE)
    activity_attachments = models.FileField(upload_to='activity_attachments', blank=True,null=True, validators=[validate_attachment])