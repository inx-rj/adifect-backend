# Generated by Django 3.2.14 on 2022-12-01 13:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0034_auto_20221122_0823'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='jobtemplate',
            name='status',
        ),
    ]
