# Generated by Django 3.2.14 on 2022-11-07 10:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0022_jobactivityattachments_jobworkattachments_memberapprovals_submitjobwork'),
    ]

    operations = [
        migrations.AddField(
            model_name='submitjobwork',
            name='submit_job_url',
            field=models.CharField(blank=True, default=None, max_length=50000, null=True),
        ),
    ]
