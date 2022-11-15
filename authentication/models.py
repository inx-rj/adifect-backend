from distutils.command.upload import upload
from pyexpat import model
from wsgiref.validate import validator
from django.db import models
from django.contrib.auth.models import AbstractUser
import os

from django.db.models import CharField
from rest_framework import serializers
from django.core.exceptions import ValidationError
from .manager import SoftDeleteManager


# Create your models here.

def validate_image(value):
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    ext = ext.strip()
    valid_extensions = ['.jpg', '.jpeg', '.png']
    if not ext.lower() in valid_extensions:
        raise ValidationError("Unsupported file extension....")
    return value


def validate_video_extension(value):
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    ext = ext.strip()
    valid_extensions = ['.mp4']
    if not ext.lower() in valid_extensions:
        raise ValidationError("Unsupported video extension....")
    return value


class CustomUser(AbstractUser):
    ROLES = ((0, 'Admin'), (1, 'Creator'), (2, 'Agency'), (3, 'Member'))

    role = models.IntegerField(choices=ROLES, default=1)
    forget_password_token = models.TextField(null=True, blank=True)
    token_expire_time = models.DateTimeField(null=True, blank=True)
    profile_title = models.CharField(max_length=200, null=True, blank=True)
    profile_description = models.TextField(null=True, blank=True)
    profile_img = models.ImageField(upload_to='user_profile_images/', null=True, blank=True,
                                    validators=[validate_image])
    video = models.FileField(upload_to='user_video/', null=True, blank=True, validators=[validate_video_extension])
    profile_status = models.CharField(choices=(('0', 'away'), ('1', 'online'), ('2', 'offline')), max_length=30,
                                      default='1', blank=True, null=True)
    preferred_communication_mode = models.CharField(
        choices=(('0', 'Email'), ('1', 'Whatsapp'), ('2', 'Skype'), ('3', 'Direct message')), max_length=30,
        default='0', blank=True, null=True)
    preferred_communication_id = models.CharField(max_length=200, null=True, blank=True)
    is_exclusive = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    availability = models.CharField(max_length=1000, null=True, blank=True)
    is_trashed = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    is_account_closed = models.BooleanField(default=False)
    sub_title = models.CharField(max_length=200, null=True, blank=True)
    Language = models.CharField(max_length=20, null=True, blank=True)
    website = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        try:
            this = CustomUser.objects.get(id=self.id)
            if this.video != self.video:
                this.video.delete()
            if this.profile_img != self.profile_img:
                this.profile_img.delete()

        except:
            pass
        super(CustomUser, self).save(*args, **kwargs)

    def __str__(self):
        return self.email


class CustomUserPortfolio(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name="Portfolio_user", blank=True,
                             null=True)
    portfolio_images = models.FileField(upload_to='user_portfolio', blank=True, null=True)

    # def save(self, *args, **kwargs):
    #     try:
    #         this = CustomUserPortfolio.objects.get(id=self.id)
    #         if this.portfolio_images != self.portfolio_images:
    #             this.portfolio_images.delete()

    #     except:
    #         pass
    #     super(CustomUserPortfolio, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return self.user.first_name

    class Meta:
        verbose_name_plural = 'CustomUser Portfolio'


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


# ---------------------------------------- Userprofile -------------------------------------------------------#

class UserProfile(BaseModel):
    class ProfileStatus(models.IntegerChoices):
        Away = 0
        Online = 1
        Offline = 2

    user = models.ForeignKey(CustomUser, related_name='user_profile', on_delete=models.SET_NULL, blank=True, null=True)
    profile_title = models.CharField(max_length=200, null=True, blank=True)
    profile_description = models.TextField(null=True, blank=True)
    profile_img = models.ImageField(upload_to='user_profile_images/', null=True, blank=True,
                                    validators=[validate_image])
    video = models.FileField(upload_to='user_video/', null=True, blank=True, validators=[validate_video_extension])
    profile_status = models.IntegerField(choices=ProfileStatus.choices, default=ProfileStatus.Online)

    def save(self, *args, **kwargs):
        try:
            this = UserProfile.objects.get(id=self.id)
            if this.video != self.video:
                this.video.delete()
            if this.profile_img != self.profile_img:
                this.profile_img.delete()

        except:
            pass
        super(UserProfile, self).save(*args, **kwargs)

    def __str__(self):
        return self.user.email


class UserCommunicationMode(BaseModel):
    class Modes(models.IntegerChoices):
        Email = 0
        Sms = 1
        WhatsApp = 2
        Slack = 3

    communication_mode = models.IntegerField(choices=Modes.choices, default=Modes.Email)
    user = models.ForeignKey(CustomUser, related_name="user_communication_mode", on_delete=models.SET_NULL, blank=True,
                             null=True)
    mode_value = models.CharField(max_length=1000, null=True, blank=True)
    is_preferred = models.BooleanField(default=False)

    def __str__(self):
        return self.user.first_name

    class Meta:
        verbose_name_plural = 'User Communication Mode'

# --------------------------------------------------- end -----------------------------------------------------------#

class PaymentMethod(BaseModel):
    name = models.CharField(max_length=200)
    public_key = models.CharField(max_length=200, null=True, blank=True)
    secret_key = models.CharField(max_length=200, null=True, blank=True)
    is_active = models.BooleanField(default=False)

    def __str__(self) -> CharField:
        return self.name

    class Meta:
        verbose_name_plural = 'Payment Method'


class PaymentDetails(BaseModel):
    clientPayerId = models.CharField(max_length=100, null=True, blank=True)
    tintype = models.CharField(max_length=200, null=True, blank=True, default='Individual')
    payerTin = models.CharField(max_length=100, null=True, blank=True)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    middle_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    suffix = models.CharField(max_length=50, null=True, blank=True)
    ssn = models.CharField(max_length=100, null=True, blank=True)

    address_1 = models.CharField(max_length=250, null=True, blank=True)
    address_2 = models.CharField(max_length=250, null=True, blank=True)
    city = models.CharField(max_length=250, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    zipcode = models.CharField(max_length=13, null=True, blank=True)

    country = models.CharField(max_length=50, null=True, blank=True, default='US')
    phone_number = models.CharField(max_length=13, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    last_filing = models.BooleanField(null=False, default=True)
    combined_fed_state_filing = models.BooleanField(null=False, default=True)

    def __str__(self) -> CharField:
        return self.first_name

    class Meta:
        verbose_name_plural = 'Payment Details'
