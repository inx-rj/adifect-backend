# Generated by Django 3.2.14 on 2022-09-14 09:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0052_auto_20220914_0952'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='company',
            name='agency',
        ),
        migrations.AlterField(
            model_name='industry',
            name='industry_name',
            field=models.CharField(max_length=50),
        ),
    ]