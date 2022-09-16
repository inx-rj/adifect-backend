# Generated by Django 3.2.14 on 2022-08-25 07:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('agency', '0008_workflow_job_owner'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='workflow',
            name='job_owner',
        ),
        migrations.AddField(
            model_name='workflow',
            name='agency',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='agency', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='workflow',
            name='user',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='user', to=settings.AUTH_USER_MODEL),
        ),
    ]