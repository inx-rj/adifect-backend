# Generated by Django 3.2.14 on 2022-08-31 10:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0018_alter_worksflow_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Stage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('is_approval', models.BooleanField(default=False)),
                ('is_observer', models.BooleanField(default=False)),
                ('approvals', models.ManyToManyField(related_name='stage_approvals', to='agency.InviteMember')),
                ('observer', models.ManyToManyField(related_name='stage_observer', to='agency.InviteMember')),
                ('workflow', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stage_workflow', to='agency.worksflow')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]