# Generated by Django 3.2.14 on 2022-10-20 14:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0018_auto_20221018_1248'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='job_due_date',
            field=models.DateField(blank=True, default=None, null=True),
        ),
    ]
