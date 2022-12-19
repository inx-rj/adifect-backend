# Generated by Django 3.2.14 on 2022-11-22 08:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0033_jobtasks_is_complete'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobworkactivity',
            name='message_work',
            field=models.CharField(blank=True, max_length=2000, null=True),
        ),
        migrations.CreateModel(
            name='JobWorkActivityAttachments',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_trashed', models.BooleanField(default=False)),
                ('work_attachment', models.FileField(blank=True, default=None, null=True, upload_to='activity_job_work_attachments')),
                ('work_activity', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='job_work_activity_attachments', to='administrator.jobworkactivity')),
            ],
            options={
                'verbose_name_plural': 'Job Work Activity Attachments',
            },
        ),
    ]