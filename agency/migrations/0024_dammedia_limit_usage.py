# Generated by Django 3.2.14 on 2022-11-10 07:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0023_remove_dammedia_limit_usage'),
    ]

    operations = [
        migrations.AddField(
            model_name='dammedia',
            name='limit_usage',
            field=models.IntegerField(default=0),
        ),
    ]
