# Generated by Django 3.2.14 on 2022-07-27 09:52

import authentication.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0011_auto_20220726_1401'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='profile_img',
            field=models.ImageField(blank=True, null=True, upload_to='user_profile_images/', validators=[authentication.models.validate_image]),
        ),
    ]
