# Generated by Django 3.2.14 on 2022-09-07 09:39

import administrator.models
import autoslug.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Activities',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_trashed', models.BooleanField(default=False)),
                ('message', models.CharField(blank=True, default=None, max_length=100, null=True)),
                ('date_time', models.DateTimeField(auto_now_add=True)),
                ('activity_type', models.CharField(choices=[('0', 'Chat'), ('1', 'Follow Up Request'), ('2', 'Rating')], default='0', max_length=30)),
            ],
            options={
                'verbose_name_plural': 'Activities',
            },
        ),
        migrations.CreateModel(
            name='ActivityAttachments',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_trashed', models.BooleanField(default=False)),
                ('activity_attachments', models.FileField(blank=True, null=True, upload_to='activity_attachments', validators=[administrator.models.validate_attachment])),
            ],
            options={
                'verbose_name_plural': 'Activity Attachments',
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_trashed', models.BooleanField(default=False)),
                ('category_name', models.CharField(max_length=50)),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='category_name')),
                ('description', models.TextField(blank=True, default=None, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name_plural': 'Category',
            },
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_trashed', models.BooleanField(default=False)),
                ('name', models.CharField(max_length=50)),
                ('description', models.CharField(max_length=200)),
                ('company_type', models.CharField(choices=[('0', 'person'), ('1', 'agency')], default='1', max_length=30)),
                ('is_active', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name_plural': 'Company',
            },
        ),
        migrations.CreateModel(
            name='Industry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_trashed', models.BooleanField(default=False)),
                ('industry_name', models.CharField(max_length=50)),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='industry_name')),
                ('description', models.TextField(blank=True, default=None, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name_plural': 'Industry',
            },
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_trashed', models.BooleanField(default=False)),
                ('title', models.CharField(max_length=250)),
                ('description', models.TextField(blank=True, default=None, null=True)),
                ('job_type', models.CharField(choices=[('0', 'Fixed'), ('1', 'Hourly')], default='0', max_length=30)),
                ('expected_delivery_date', models.DateField(default=None)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('tags', models.CharField(max_length=10000)),
                ('image_url', models.CharField(blank=True, default=None, max_length=50000, null=True)),
                ('sample_work_url', models.CharField(blank=True, default=None, max_length=50000, null=True)),
                ('status', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                'verbose_name_plural': 'Job',
            },
        ),
        migrations.CreateModel(
            name='JobApplied',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_trashed', models.BooleanField(default=False)),
                ('cover_letter', models.TextField()),
                ('job_bid_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('duration', models.CharField(blank=True, default=None, max_length=200, null=True)),
                ('links', models.CharField(blank=True, default=None, max_length=50000, null=True)),
                ('offer_price', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=10, null=True)),
                ('due_date', models.DateField(blank=True, default=None, null=True)),
                ('proposed_price', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=10, null=True)),
                ('proposed_due_date', models.DateField(blank=True, default=None, null=True)),
                ('status', models.IntegerField(choices=[(0, 'Applied'), (1, 'In Review'), (2, 'Hire')], default=0)),
                ('job_applied_date', models.DateField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'Jobs Applied',
            },
        ),
        migrations.CreateModel(
            name='JobAppliedAttachments',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_trashed', models.BooleanField(default=False)),
                ('job_applied_attachments', models.FileField(blank=True, null=True, upload_to='job_applied_attachments')),
            ],
            options={
                'verbose_name_plural': 'Job Applied Attachments',
            },
        ),
        migrations.CreateModel(
            name='JobAttachments',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_trashed', models.BooleanField(default=False)),
                ('job_images', models.FileField(blank=True, null=True, upload_to='job_images')),
                ('work_sample_images', models.FileField(blank=True, null=True, upload_to='work_sample_images')),
            ],
            options={
                'verbose_name_plural': 'Job Attachments',
            },
        ),
        migrations.CreateModel(
            name='JobHired',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_trashed', models.BooleanField(default=False)),
                ('hire_date', models.DateField(auto_now_add=True)),
                ('status', models.CharField(choices=[('0', 'In progress'), ('1', 'In Review'), ('2', 'Completed'), ('3', 'Closed')], default='0', max_length=30)),
            ],
            options={
                'verbose_name_plural': 'Jobs Hired',
            },
        ),
        migrations.CreateModel(
            name='Level',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_trashed', models.BooleanField(default=False)),
                ('level_name', models.CharField(max_length=50)),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='level_name')),
                ('description', models.TextField(blank=True, default=None, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name_plural': 'Level',
            },
        ),
        migrations.CreateModel(
            name='PreferredLanguage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_trashed', models.BooleanField(default=False)),
                ('ln_code', models.CharField(max_length=100)),
                ('ln_proficiency', models.IntegerField(choices=[(0, 'Basic'), (1, 'Intermediate'), (2, 'Fluent')], default=0)),
            ],
            options={
                'verbose_name_plural': 'Preferred Languages',
            },
        ),
        migrations.CreateModel(
            name='Skills',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_trashed', models.BooleanField(default=False)),
                ('skill_name', models.CharField(max_length=50, unique=True)),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='skill_name')),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name_plural': 'Skills',
            },
        ),
    ]
