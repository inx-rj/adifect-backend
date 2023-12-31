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
from agency.models import WorksFlow, Company, Industry, InviteMember, Workflow_Stages, InviteMember
from django.core.validators import MaxValueValidator, MinValueValidator
from io import BytesIO
from PIL import Image
import sys
from django.core.files.uploadedfile import InMemoryUploadedFile


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


# -------------------------------- old ---------------------------------------------#
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

    MEDIA = 0
    SMS = 1
    TEXT_COPY = 2

    CREATE_JOB_TYPE_CHOICES = [
        (MEDIA, "media"),
        (SMS, "sms"),
        (TEXT_COPY, "text copy")
    ]

    title = models.CharField(max_length=250)
    create_job_type = models.PositiveSmallIntegerField(choices=CREATE_JOB_TYPE_CHOICES, default=MEDIA)
    description = models.TextField(default=None, blank=True, null=True)
    job_type = models.CharField(choices=jobType, max_length=30, default='0', null=True, blank=True)
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True, blank=True)
    expected_delivery_date = models.DateField(default=None, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None)
    tags = models.CharField(max_length=10000, null=True, blank=True)
    skills = models.ManyToManyField(Skills, blank=True)
    image_url = models.CharField(default=None, max_length=50000, blank=True, null=True)
    sample_work_url = models.CharField(default=None, max_length=50000, blank=True, null=True)
    related_jobs = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, related_name="job_company", null=True, blank=True)
    industry = models.ForeignKey(Industry, on_delete=models.SET_NULL, related_name="job_industry", null=True,
                                 blank=True)
    workflow = models.ForeignKey(WorksFlow, on_delete=models.SET_NULL, related_name="job_workflow", blank=True,
                                 null=True)
    job_due_date = models.DateField(default=None, null=True, blank=True)
    due_date_index = models.IntegerField(null=True, blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name="Job_user", null=True, blank=True)
    template_name = models.CharField(max_length=250, null=True, blank=True)
    status = models.IntegerField(choices=Status.choices, default=Status.Post)
    is_active = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False)
    is_house_member = models.BooleanField(default=False)
    house_member = models.ManyToManyField(InviteMember, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name="Job_created_by", null=True,
                                   blank=True)
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name="Job_assigned_by", null=True,
                                    blank=True)

    class Meta:
        verbose_name_plural = 'Job'

    def clean(self):
        exist_job = Job.objects.filter(template_name=self.template_name, is_trashed=False).exclude(template_name=None)
        if self.id:
            exist_job = exist_job.exclude(pk=self.id)
        if exist_job:
            raise ValidationError("Job Template With This Name Already Exist")

    def save(self, *args, **kwargs):
        self.job_due_date = self.expected_delivery_date
        super(Job, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.title}'


class JobAttachments(BaseModel):
    job = models.ForeignKey(Job, related_name="images", on_delete=models.SET_NULL, null=True, blank=True)
    job_images = models.FileField(upload_to='job_images', blank=True, null=True)
    job_images_thumbnail = models.FileField(upload_to="job_images_thumbnail", blank=True, null=True)
    work_sample_images = models.FileField(upload_to='work_sample_images', blank=True, null=True)
    work_sample_thumbnail = models.FileField(upload_to="work_sample_images_thumbnail", blank=True, null=True)
    dam_media_id = models.ForeignKey("agency.DamMedia", on_delete=models.SET_NULL, null=True, blank=True)
    is_video = models.BooleanField(default=False)

    def save(self, **kwargs):
        output_size = (250, 250)
        output_thumb = BytesIO()
        if self.job_images:
            if str(self.job_images).endswith((".mp4", ".mp3", ".mov", ".MP4", ".MP3", ".MOV")):
                self.job_images_thumbnail = self.job_images
                self.is_video = True
            else:
                img = Image.open(self.job_images)
                img_name = self.job_images.name.split('.')[0]
                img.thumbnail(output_size)
                img.save(output_thumb, format=img.format, quality=90)

                self.job_images_thumbnail = InMemoryUploadedFile(output_thumb, 'ImageField', f"{img_name}_thumb.jpg",
                                                                 'image/jpeg',
                                                                 sys.getsizeof(output_thumb), None)
        if self.work_sample_images:
            if str(self.work_sample_images).endswith((".mp4", ".mp3", ".mov")):
                self.work_sample_thumbnail = self.work_sample_images
                self.is_video = True
            else:
                img_work_sample = Image.open(self.work_sample_images)
                img_name = self.work_sample_images.name.split('.')[0]
                print(img_name)
                img_work_sample.thumbnail(output_size)
                img_work_sample.save(output_thumb, format=img_work_sample.format, quality=90)

                self.work_sample_thumbnail = InMemoryUploadedFile(output_thumb, 'ImageField', f"{img_name}_thumb.jpg",
                                                                  'image/jpeg',
                                                                  sys.getsizeof(output_thumb), None)

        super(JobAttachments, self).save()

    def __str__(self) -> str:
        return f'{self.job}'

    class Meta:
        verbose_name_plural = 'Job Attachments'


class JobActivity(BaseModel):
    class Status(models.IntegerChoices):
        Notification = 0
        Chat = 1
        JobWork = 2
        WorkStage = 3

    class Type(models.IntegerChoices):
        Create = 0
        Updated = 1
        Proposal = 2
        Accept = 3
        Reject = 4
        Moved = 5
        Completed = 6
        Rating = 7

    class Send_by(models.IntegerChoices):
        agency = 0
        creator = 1

    job = models.ForeignKey(Job, related_name="activity_job", on_delete=models.SET_NULL, null=True, blank=True)
    activity_type = models.IntegerField(choices=Type.choices, null=True, blank=True)
    # activity_type = models.IntegerField(choices=Type.choices, default=Type.Create)
    user = models.ForeignKey(CustomUser, related_name='job_activity_user', on_delete=models.SET_NULL, null=True,
                             blank=True)
    activity_status = models.IntegerField(choices=Status.choices, default=Status.Notification)
    activity_by = models.IntegerField(choices=Send_by.choices, default=Send_by.agency)

    def __str__(self) -> str:
        return f'{self.job.title}'

    class Meta:
        verbose_name_plural = 'Job Activities'


class JobActivityChat(BaseModel):
    job_activity = models.ForeignKey(JobActivity, related_name="activity_job_chat", on_delete=models.SET_NULL,
                                     null=True, blank=True)
    sender = models.ForeignKey(CustomUser, related_name="job_activity_chat_sender", on_delete=models.SET_NULL,
                               null=True, blank=True)
    receiver = models.ForeignKey(CustomUser, related_name="job_activity_chat_receiver", on_delete=models.SET_NULL,
                                 null=True, blank=True)
    messages = models.CharField(max_length=2000, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f'{self.messages}'

    class Meta:
        verbose_name_plural = 'Job Activities Chat'


class JobActivityAttachments(BaseModel):
    job_activity_chat = models.ForeignKey(JobActivityChat, related_name="activity_job_attachments",
                                          on_delete=models.SET_NULL, null=True, blank=True)
    chat_attachment = models.FileField(upload_to='activity_chat_attachments', default=None, blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Job Activity Attachments'


class JobWorkActivity(BaseModel):
    Activity_choice = (
        ('approved', "approved"),
        ('rejected', 'rejected'),
        ('moved', 'moved'),
        ('submit_approval', 'submit_approval')
    )

    job_activity_chat = models.ForeignKey(JobActivity, related_name="activity_job_work",
                                          on_delete=models.SET_NULL, null=True, blank=True)
    job_work = models.ForeignKey('SubmitJobWork', related_name='job_work_activity', on_delete=models.SET_NULL,
                                 null=True, blank=True)
    approver = models.ForeignKey('MemberApprovals', related_name='job_approver_activity', on_delete=models.SET_NULL,
                                 null=True, blank=True)
    workflow_stage = models.ForeignKey(Workflow_Stages, related_name="job_activity_stages", on_delete=models.SET_NULL,
                                       null=True, blank=True)
    work_activity = models.CharField(
        max_length=30,
        choices=Activity_choice,
        null=True, blank=True
    )
    message_work = models.CharField(max_length=2000, blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Job Work Activity'


class JobWorkActivityAttachments(BaseModel):
    work_activity = models.ForeignKey(JobWorkActivity, related_name='job_work_activity_attachments',
                                      on_delete=models.SET_NULL, null=True, blank=True)
    work_attachment = models.FileField(upload_to='activity_job_work_attachments', default=None, blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Job Work Activity Attachments'


class JobApplied(BaseModel):
    class Status(models.IntegerChoices):
        APPLIED = 0
        REJECT = 1
        HIRE = 2
        IN_REVIEW = 3
        Completed = 4

    cover_letter = models.TextField(default=None, null=True, blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    job = models.ForeignKey(Job, related_name='job_applied', default=None, on_delete=models.SET_NULL, null=True,
                            blank=True)
    job_bid_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # duration = models.CharField(max_length=200, default=None, null=True, blank=True)
    links = models.CharField(default=None, max_length=50000, blank=True, null=True)
    offer_price = models.DecimalField(default=None, max_digits=10, decimal_places=2, blank=True, null=True)
    due_date = models.DateField(default=None, blank=True, null=True)
    proposed_price = models.DecimalField(default=None, max_digits=10, decimal_places=2, blank=True, null=True)
    proposed_due_date = models.DateField(default=None, blank=True, null=True)
    question = models.TextField(default=None, null=True, blank=True)
    status = models.IntegerField(choices=Status.choices, default=Status.APPLIED)
    job_applied_date = models.DateField(auto_now_add=True)
    Accepted_proposal_date = models.DateTimeField(editable=False, default=None, null=True, blank=True)
    is_seen = models.BooleanField(default=False)
    is_modified = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Jobs Applied'

    def save(self, *args, **kwargs):
        if self.proposed_price is None:
            self.proposed_price = self.job.price
        super(JobApplied, self).save(*args, **kwargs)


class JobAppliedAttachments(BaseModel):
    job_applied = models.ForeignKey(JobApplied, related_name="images", on_delete=models.SET_NULL, null=True, blank=True)
    job_applied_attachments = models.FileField(upload_to='job_applied_attachments', blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Job Applied Attachments'


# class JobHired(BaseModel):
#     user = models.ManyToManyField(CustomUser)
#     job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True)
#     hire_date = models.DateField(auto_now_add=True)
#     status = models.CharField(choices=(('0', 'In progress'), ('1', 'In Review'), ('2', 'Completed'), ('3', 'Closed')),
#                               max_length=30, default='0')
#
#     class Meta:
#         verbose_name_plural = 'Jobs Hired'


# class Activities(BaseModel):
#     job_id = models.ForeignKey(Job, on_delete=models.SET_NULL, related_name="job_id", db_column='job_id', null=True,
#                                blank=True)
#     hired_user = models.ForeignKey(JobHired, on_delete=models.SET_NULL, null=True, blank=True)
#     message = models.CharField(max_length=100, default=None, blank=True, null=True)
#     date_time = models.DateTimeField(auto_now_add=True, editable=False)
#     activity_type = models.CharField(choices=(('0', 'Chat'), ('1', 'Follow Up Request'), ('2', 'Rating')),
#                                      max_length=30, default='0')
#     sender = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="sender_id")
#
#     class Meta:
#         verbose_name_plural = 'Activities'
#
#
# class ActivityAttachments(BaseModel):
#     activities = models.ForeignKey(Activities, related_name="images", on_delete=models.SET_NULL, null=True, blank=True)
#     activity_attachments = models.FileField(upload_to='activity_attachments', blank=True, null=True,
#                                             validators=[validate_attachment])
#
#     class Meta:
#         verbose_name_plural = 'Activity Attachments'


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
    is_complete = models.BooleanField(default=False)

    def __str__(self) -> CharField:
        return self.title

    class Meta:
        verbose_name_plural = 'Job Task'


class JobTemplate(BaseModel):
    class JobType(models.IntegerChoices):
        Fixed = 0
        Hourly = 1

    # class Status(models.IntegerChoices):
    #     Draft = 0
    #     Template = 1
    #     Post = 2

    template_name = models.CharField(max_length=250)
    title = models.CharField(max_length=250)
    description = models.TextField(default=None, blank=True, null=True)
    job_type = models.IntegerField(choices=JobType.choices, default=JobType.Fixed)
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, related_name="jobtemplate_level", null=True, blank=True)
    expected_delivery_date = models.DateField(default=None)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None)
    tags = models.CharField(max_length=10000, null=True, blank=True)
    skills = models.ManyToManyField(Skills, blank=True)
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

    is_house_member = models.BooleanField(default=False)
    house_member = models.ManyToManyField(InviteMember, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name="Job_template_created_by",
                                   null=True, blank=True)
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name="Job_template_assigned_by",
                                    null=True, blank=True)

    # status = models.IntegerField(choices=Status.choices, default=Status.Template)

    class Meta:
        verbose_name_plural = 'Job Template'

    def clean(self):
        exist_job = JobTemplate.objects.filter(template_name=self.template_name, is_trashed=False).exclude(
            template_name=None)
        if self.id:
            exist_job = exist_job.exclude(pk=self.id)
        if exist_job:
            raise ValidationError("Job Template With This Name Already Exist")

    def __str__(self) -> str:
        return f'{self.template_name}'


class JobTemplateTasks(BaseModel):
    job_template = models.ForeignKey(JobTemplate, related_name="jobtemplate_tasks", on_delete=models.SET_NULL,
                                     null=True, blank=True)
    title = models.CharField(max_length=3000, null=False, blank=False)
    due_date = models.DateField(auto_now_add=False)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> CharField:
        return self.title

    class Meta:
        verbose_name_plural = 'Job Template Task'


class JobTemplateAttachments(BaseModel):
    job_template = models.ForeignKey(JobTemplate, related_name="job_template_images", on_delete=models.SET_NULL,
                                     null=True, blank=True)
    job_template_images = models.FileField(upload_to='job_template_image', blank=True, null=True)
    work_sample_images = models.FileField(upload_to='job_template_sample_image', blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Job Template_Attachments'


# ------ avneet ----#
class Question(BaseModel):
    question = models.TextField(default=None, null=True, blank=True)
    job_applied = models.ForeignKey(JobApplied, on_delete=models.SET_NULL, related_name="question_job_applied",
                                    blank=True, null=True)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name="question_user", blank=True, null=True)
    status = models.IntegerField(default=2)

    def __str__(self) -> str:
        return f'{self.question}'


class Answer(BaseModel):
    question = models.ForeignKey(Question, on_delete=models.SET_NULL, related_name="answer_question", blank=True,
                                 null=True)
    answer = models.CharField(max_length=200)
    job_applied = models.ForeignKey(JobApplied, on_delete=models.SET_NULL, related_name="answer_job_applied",
                                    blank=True, null=True)
    agency = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name="answer_agency", blank=True,
                               null=True)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name="answer_user", blank=True, null=True)

    def __str__(self) -> str:
        return f'{self.answer}'


class UserSkills(BaseModel):
    user = models.ForeignKey(CustomUser, related_name="skills_user", on_delete=models.SET_NULL, null=True)
    skills = models.ForeignKey(Skills, related_name="user_skill", on_delete=models.SET_NULL, null=True)
    skill_rating = models.FloatField(default=None, null=True, validators=[
        MaxValueValidator(5.0),
        MinValueValidator(0.1)
    ]
                                     )

    def __str__(self) -> str:
        return f'{self.skills.skill_name if self.skills is not None else ""}'


class SubmitJobWork(BaseModel):
    class Status(models.IntegerChoices):
        Approved = 1
        Rejected = 2
        Pending = 0

    job_applied = models.ForeignKey(JobApplied, related_name="submit_work", on_delete=models.SET_NULL, blank=True,
                                    null=True)
    message = models.CharField(max_length=5000, blank=True, null=True)
    submit_job_url = models.CharField(default=None, max_length=50000, blank=True, null=True)
    task = models.ForeignKey(JobTasks, related_name="submit_task", on_delete=models.SET_NULL, blank=True, null=True)
    status = models.IntegerField(choices=Status.choices, default=Status.Pending)

    class Meta:
        verbose_name_plural = 'Submit Job Work'


class JobWorkAttachments(BaseModel):
    job_work = models.ForeignKey(SubmitJobWork, related_name="job_submit_Work", on_delete=models.SET_NULL,
                                 null=True, blank=True)
    work_attachments = models.FileField(upload_to='work_attachments', blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Job Works Attachments'


class MemberApprovals(BaseModel):
    class Status(models.IntegerChoices):
        Approved = 1
        Rejected = 2
        Pending = 0

    job_work = models.ForeignKey(SubmitJobWork, related_name="job_submit", on_delete=models.SET_NULL,
                                 null=True, blank=True)
    approver = models.ForeignKey(InviteMember, related_name="job_approvers", on_delete=models.SET_NULL,
                                 null=True, blank=True)
    status = models.IntegerField(choices=Status.choices, default=Status.Pending)
    message = models.TextField(default=None, blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    workflow_stage = models.ForeignKey(Workflow_Stages, related_name="job_stages", on_delete=models.SET_NULL,
                                       null=True, blank=True)
    nudge_status = models.CharField(default='', max_length=50000, blank=True, null=True)
    work_attachment = models.FileField(upload_to='member_approval_job_work_attachments', default=None, blank=True,
                                       null=True)

    class Meta:
        verbose_name_plural = 'Member Approvals'


class JobFeedback(BaseModel):
    receiver_user = models.ForeignKey(CustomUser, related_name='feedback_receiver', on_delete=models.CASCADE, null=True,
                                      blank=True, default=None)
    sender_user = models.ForeignKey(CustomUser, related_name='feedback_sender', on_delete=models.CASCADE, null=True,
                                    blank=True, default=None)
    rating = models.IntegerField(default=None, null=True, blank=True, validators=[
        MaxValueValidator(5)])
    feedback = models.TextField(default=None, null=True, blank=True)
    job = models.ForeignKey(Job, related_name='job_feedback', on_delete=models.CASCADE, blank=True, null=True,
                            default=None)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Job Feedback'


class Help(BaseModel):
    user = models.ForeignKey(CustomUser, related_name='help', on_delete=models.CASCADE, blank=True, null=True)
    subject = models.CharField(max_length=500, blank=True, null=True, default=None)
    message = models.TextField(default=None, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Help'


class HelpAttachments(BaseModel):
    attachment = models.ForeignKey(Help, related_name="help_attachments", on_delete=models.SET_NULL, null=True,
                                   blank=True)
    help_new_attachments = models.FileField(upload_to='help_attachments', default=None, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Help Attachments'


class HelpChat(BaseModel):
    help = models.ForeignKey(Help, related_name='helpChat_user', on_delete=models.CASCADE, blank=True, null=True)
    sender = models.ForeignKey(CustomUser, related_name='sender_user', on_delete=models.CASCADE, blank=True, null=True)
    receiver = models.ForeignKey(CustomUser, related_name='receiver_user', on_delete=models.CASCADE, blank=True,
                                 null=True)
    chat = models.TextField(default=None, null=True, blank=True)
    is_admin = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Help Chat'


class HelpChatAttachments(BaseModel):
    chat_attachments = models.ForeignKey(HelpChat, related_name='chat_attachments_user', on_delete=models.CASCADE,
                                         blank=True, null=True)
    chat_new_attachments = models.FileField(upload_to='helpchat_attachments', default=None, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Help Chat Attachments'
