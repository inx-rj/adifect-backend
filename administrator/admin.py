# from logging import _Level
from django.contrib import admin
from .models import Category, Job, JobAttachments, JobApplied, Industry, Skills, Company, Level, JobHired, Activities, JobAppliedAttachments, ActivityAttachments

# Register your models here.


admin.site.register(Category)

admin.site.register(Job)

admin.site.register(JobAttachments)

admin.site.register(JobApplied)

admin.site.register(Industry)

admin.site.register(Skills)

admin.site.register(Level)

admin.site.register(Company)

admin.site.register(JobHired)

admin.site.register(Activities)

admin.site.register(JobAppliedAttachments)

admin.site.register(ActivityAttachments)
