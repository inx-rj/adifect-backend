# Generated by Django 3.2.14 on 2022-09-08 11:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0056_auto_20220908_0703'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobTasks',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_trashed', models.BooleanField(default=False)),
                ('title', models.CharField(max_length=3000)),
                ('due_date', models.DateField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('job', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='jobtasks_job', to='administrator.job')),
            ],
            options={
                'verbose_name_plural': 'Job Task',
            },
        ),
    ]
