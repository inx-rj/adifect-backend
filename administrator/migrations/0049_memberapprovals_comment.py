# Generated by Django 3.2.14 on 2023-07-14 07:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0048_alter_jobworkactivity_work_activity'),
    ]

    operations = [
        migrations.AddField(
            model_name='memberapprovals',
            name='comment',
            field=models.TextField(blank=True, null=True),
        ),
    ]
