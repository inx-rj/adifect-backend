# Generated by Django 3.2.14 on 2022-11-10 10:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0025_alter_dammedia_limit_usage'),
    ]

    operations = [
        migrations.AddField(
            model_name='dammedia',
            name='job_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='dammedia',
            name='limit_usage',
            field=models.IntegerField(default=0),
        ),
    ]
