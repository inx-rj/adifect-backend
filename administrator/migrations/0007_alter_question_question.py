# Generated by Django 3.2.14 on 2022-10-03 08:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0006_auto_20221001_1347'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='question',
            field=models.TextField(blank=True, default=None, null=True),
        ),
    ]
