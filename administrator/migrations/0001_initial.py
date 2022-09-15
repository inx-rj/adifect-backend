# Generated by Django 3.2.14 on 2022-08-22 10:04

import autoslug.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('category_name', models.CharField(max_length=50)),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='category_name')),
                ('description', models.TextField(blank=True, default=None, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=50)),
                ('description', models.CharField(max_length=200)),
                ('company_type', models.CharField(choices=[('0', 'person'), ('1', 'agency')], default='1', max_length=30)),
                ('is_active', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Company',
            },
        ),
        migrations.CreateModel(
            name='Industry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('industry_name', models.CharField(max_length=50)),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='industry_name')),
                ('description', models.TextField(blank=True, default=None, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=250)),
                ('description', models.TextField(blank=True, default=None, null=True)),
                ('job_type', models.CharField(choices=[('0', 'Fixed'), ('1', 'Hourly')], default='0', max_length=30)),
                ('expected_delivery_date', models.DateField(default=None)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('tags', models.CharField(max_length=10000)),
                ('status', models.PositiveSmallIntegerField(default=0)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='administrator.category')),
                ('company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='administrator.company')),
                ('industry', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='administrator.industry')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Level',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('level_name', models.CharField(max_length=50)),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='level_name')),
                ('description', models.TextField(blank=True, default=None, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Skills',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('skill_name', models.CharField(max_length=50, unique=True)),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='skill_name')),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Stages',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('stage_name', models.CharField(max_length=50)),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='stage_name')),
                ('description', models.TextField(blank=True, default=None, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WorkFlowLevels',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('level_name', models.CharField(default=None, max_length=50)),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='level_name')),
                ('description', models.TextField(blank=True, default=None, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WorkFlow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='administrator.workflowlevels')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='JobHired',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hire_date', models.DateField(auto_now_add=True)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='administrator.job')),
                ('user', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Jobs Hired',
            },
        ),
        migrations.CreateModel(
            name='JobAttachments',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('job_images', models.FileField(blank=True, null=True, upload_to='job_images')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='administrator.job')),
            ],
        ),
        migrations.CreateModel(
            name='JobApplied',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cover_letter', models.TextField()),
                ('job_bid_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('duration', models.CharField(blank=True, default=None, max_length=200, null=True)),
                ('status', models.CharField(choices=[('0', 'Applied'), ('1', 'In Review'), ('2', 'Hire')], default='0', max_length=30)),
                ('job_applied_date', models.DateField(auto_now_add=True)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='administrator.job')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Jobs Applied',
            },
        ),
        migrations.AddField(
            model_name='job',
            name='level',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='administrator.level'),
        ),
        migrations.AddField(
            model_name='job',
            name='related_jobs',
            field=models.ManyToManyField(blank=True, related_name='_administrator_job_related_jobs_+', to='administrator.Job'),
        ),
        migrations.AddField(
            model_name='job',
            name='skills',
            field=models.ManyToManyField(to='administrator.Skills'),
        ),
        migrations.AddField(
            model_name='job',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='Activities',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.CharField(max_length=200)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('is_read', models.BooleanField(default=False)),
                ('hired_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities_hired_user', to=settings.AUTH_USER_MODEL)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities_job', to='administrator.job')),
                ('job_owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities_job_owner', to=settings.AUTH_USER_MODEL)),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities_sender', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Activities',
            },
        ),
    ]
