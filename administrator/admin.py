# from logging import _Level
from django.contrib import admin
from .models import Category, Job, JobAttachments, JobApplied, Skills, Level, JobHired, Activities, JobAppliedAttachments, ActivityAttachments, PreferredLanguage,JobTasks, JobTemplate,JobTemplateAttachments, Question, Answer,UserSkills

# Register your models here.


admin.site.register(Category)

admin.site.register(Job)

admin.site.register(JobAttachments)

admin.site.register(JobApplied)

admin.site.register(Skills)

admin.site.register(Level)

admin.site.register(JobHired)

admin.site.register(Activities)

admin.site.register(JobAppliedAttachments)

admin.site.register(ActivityAttachments)

admin.site.register(PreferredLanguage)

admin.site.register(JobTasks)

admin.site.register(JobTemplate)

admin.site.register(JobTemplateAttachments)

admin.site.register(Question)

admin.site.register(Answer)

admin.site.register(UserSkills)


