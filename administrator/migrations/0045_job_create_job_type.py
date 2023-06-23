# Generated by Django 3.2.14 on 2023-06-07 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0044_jobattachments_is_video'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='create_job_type',
            field=models.PositiveSmallIntegerField(choices=[(0, 'media'), (1, 'sms'), (2, 'text copy')], default=0),
        ),
    ]