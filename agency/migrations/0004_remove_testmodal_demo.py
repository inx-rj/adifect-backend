# Generated by Django 4.1.1 on 2022-09-27 07:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0003_testmodal_demo'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='testmodal',
            name='demo',
        ),
    ]