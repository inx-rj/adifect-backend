# Generated by Django 3.2.14 on 2023-06-09 09:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('intake_forms', '0004_auto_20230609_0737'),
    ]

    operations = [
        migrations.AlterField(
            model_name='intakeform',
            name='title',
            field=models.CharField(max_length=200),
        ),
    ]
