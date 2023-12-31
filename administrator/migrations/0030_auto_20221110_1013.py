# Generated by Django 3.2.14 on 2022-11-10 10:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0029_alter_jobactivity_activity_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobattachments',
            name='job_images_thumbnail',
            field=models.FileField(blank=True, null=True, upload_to='job_images_thumbnail'),
        ),
        migrations.AddField(
            model_name='jobattachments',
            name='work_sample_thumbnail',
            field=models.FileField(blank=True, null=True, upload_to='work_sample_images_thumbnail'),
        ),
    ]
