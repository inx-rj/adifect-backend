# Generated by Django 3.2.14 on 2022-08-24 07:45

import administrator.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0014_remove_activities_activity_attachment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activityattachments',
            name='activity_attachments',
            field=models.FileField(blank=True, null=True, upload_to='activity_attachments', validators=[administrator.models.validate_attachment]),
        ),
    ]
