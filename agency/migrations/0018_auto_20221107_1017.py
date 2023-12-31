# Generated by Django 3.2.14 on 2022-11-07 10:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0017_auto_20221106_1131'),
    ]

    operations = [
        migrations.AddField(
            model_name='dammedia',
            name='usage_limit_reached',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='dammedia',
            name='limit_usage',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
    ]
