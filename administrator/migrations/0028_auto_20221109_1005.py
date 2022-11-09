# Generated by Django 3.2.14 on 2022-11-09 10:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0020_auto_20221108_1117'),
        ('administrator', '0027_auto_20221108_1419'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='jobworkattachments',
            options={'verbose_name_plural': 'Job Works Attachments'},
        ),
        migrations.AlterField(
            model_name='jobactivity',
            name='activity_status',
            field=models.IntegerField(choices=[(0, 'Notification'), (1, 'Chat'), (2, 'Jobwork'), (3, 'Workstage')], default=0),
        ),
        migrations.CreateModel(
            name='JobWorkActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_trashed', models.BooleanField(default=False)),
                ('work_activity', models.CharField(blank=True, choices=[('approved', 'approved'), ('rejected', 'rejected'), ('moved', 'moved'), ('submit_approval', 'submit_approval')], max_length=30, null=True)),
                ('approver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='job_approver_activity', to='administrator.memberapprovals')),
                ('job_activity_chat', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='activity_job_work', to='administrator.jobactivity')),
                ('job_work', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='job_work_activity', to='administrator.submitjobwork')),
                ('workflow_stage', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='job_activity_stages', to='agency.workflow_stages')),
            ],
            options={
                'verbose_name_plural': 'Job Work Activity',
            },
        ),
    ]