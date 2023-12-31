# Generated by Django 3.2.14 on 2022-12-09 12:25

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('administrator', '0038_auto_20221207_1243'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobFeedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_trashed', models.BooleanField(default=False)),
                ('rating', models.IntegerField(blank=True, default=None, null=True, validators=[django.core.validators.MaxValueValidator(5)])),
                ('feedback', models.TextField(blank=True, default=None, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('job', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='job_feedback', to='administrator.job')),
                ('receiver_user', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='feedback_receiver', to=settings.AUTH_USER_MODEL)),
                ('sender_user', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='feedback_sender', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Job Feedback',
            },
        ),
    ]
