# Generated by Django 3.2.14 on 2022-11-30 10:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0032_auto_20221130_1027'),
    ]

    operations = [
        migrations.RenameField(
            model_name='workflow_stages',
            old_name='approval_times',
            new_name='approval_time',
        ),
    ]
