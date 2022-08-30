from distutils.command.upload import upload
from pyexpat import model
from wsgiref.validate import validator
from django.db import models
from django.contrib.auth.models import AbstractUser
import os
from rest_framework import serializers
from django.core.exceptions import ValidationError

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

    ROLES = ((1, 'Creator'), (2, 'Agency'))    

    role = models.IntegerField(choices=ROLES, default=1)
    forget_password_token = models.TextField(null=True, blank=True)
    token_expire_time = models.DateTimeField(null=True, blank=True)
    profile_title = models.CharField(max_length=200, null=True, blank=True)
    profile_description = models.TextField(null=True, blank=True)
    profile_img = models.ImageField(upload_to='user_profile_images/', null=True, blank=True, validators=[validate_image])
    video = models.FileField(upload_to='user_video/',null=True, blank=True, validators=[validate_video_extension])
    profile_status = models.CharField(choices=(('0', 'away'), ('1', 'online'), ('2','offline')), max_length=30, default='1',blank=True,null=True)
    preferred_communication_mode = models.CharField(choices=(('0', 'Email'), ('1', 'Whatsapp'), ('2','Skype'), ('3','Direct message')), max_length=30, default='0',blank=True,null=True)
    is_exclusive = models.BooleanField(default=False)
    

    def save(self, *args, **kwargs):
        try:
            this = CustomUser.objects.get(id=self.id)
            if this.video != self.video:
                this.video.delete()
            if this.profile_img != self.profile_img:
                this.profile_img.delete()
            
        except: pass
        super(CustomUser, self).save(*args, **kwargs)

    def __str__(self):
        return self.email



class CustomUserPortfolio(models.Model):
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    portfolio_images = models.FileField(upload_to='user_portfolio', blank=True,null=True)

    def save(self, *args, **kwargs):
        try:
            this = CustomUserPortfolio.objects.get(id=self.id)
            if this.portfolio_images != self.portfolio_images:
                this.portfolio_images.delete()
            
        except: pass
        super(CustomUserPortfolio, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return self.user
