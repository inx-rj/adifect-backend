# Generated by Django 3.2.14 on 2022-11-04 14:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0015_auto_20221102_1014'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dam',
            name='name',
            field=models.CharField(blank=True, default=None, max_length=5000, null=True),
        ),
        migrations.AlterField(
            model_name='dammedia',
            name='description',
            field=models.CharField(blank=True, default=None, max_length=5000, null=True),
        ),
        migrations.AlterField(
            model_name='dammedia',
            name='title',
            field=models.CharField(blank=True, default=None, max_length=5000, null=True),
        ),
    ]
