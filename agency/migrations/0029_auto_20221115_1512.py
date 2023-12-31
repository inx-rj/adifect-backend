# Generated by Django 3.2.14 on 2022-11-15 15:12

import authentication.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0028_alter_dam_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='company_email',
            field=models.EmailField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='company_phone_number',
            field=models.CharField(blank=True, help_text='Enter valid phone number.', max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='company_profile_img',
            field=models.ImageField(blank=True, null=True, upload_to='company_image/', validators=[authentication.models.validate_image]),
        ),
        migrations.AddField(
            model_name='company',
            name='company_website',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]
