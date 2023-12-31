# Generated by Django 3.2.14 on 2022-10-14 13:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0014_alter_jobapplied_job'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_trashed', models.BooleanField(default=False)),
                ('activity_type', models.IntegerField(choices=[(0, 'Create'), (1, 'Updated'), (2, 'Proposal'), (3, 'Accept'), (4, 'Reject')], default=0)),
                ('job', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='activity_job', to='administrator.job')),
            ],
            options={
                'verbose_name_plural': 'Job Activities',
            },
        ),
        migrations.RemoveField(
            model_name='activityattachments',
            name='activities',
        ),
        migrations.RemoveField(
            model_name='jobhired',
            name='job',
        ),
        migrations.RemoveField(
            model_name='jobhired',
            name='user',
        ),
        migrations.AddField(
            model_name='jobapplied',
            name='is_modified',
            field=models.BooleanField(default=False),
        ),
        migrations.DeleteModel(
            name='Activities',
        ),
        migrations.DeleteModel(
            name='ActivityAttachments',
        ),
        migrations.DeleteModel(
            name='JobHired',
        ),
    ]
