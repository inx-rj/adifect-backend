# Generated by Django 3.2.14 on 2022-08-24 09:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0015_alter_activityattachments_activity_attachments'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobhired',
            name='status',
            field=models.CharField(choices=[('0', 'In progress'), ('1', 'In Review'), ('2', 'Completed'), ('3', 'Closed')], default='0', max_length=30),
        ),
    ]