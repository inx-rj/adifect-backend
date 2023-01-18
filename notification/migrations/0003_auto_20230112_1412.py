# Generated by Django 3.2.14 on 2023-01-12 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0002_testmedia'),
    ]

    operations = [
        migrations.AddField(
            model_name='notifications',
            name='notification_type',
            field=models.CharField(choices=[('job_edited', 'job_edited'), ('job_proposal', 'job_proposal'), ('job_submit_work', 'job_submit_work'), ('job_work_approver', 'job_work_approver'), ('job_completed', 'job_completed'), ('in_house_assigned', 'in_house_assigned'), ('invite_accepted', 'invite_accepted')], default='job_proposal', max_length=60),
        ),
        migrations.AddField(
            model_name='notifications',
            name='redirect_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
