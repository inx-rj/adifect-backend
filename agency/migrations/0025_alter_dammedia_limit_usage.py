# Generated by Django 3.2.14 on 2022-11-10 07:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0024_dammedia_limit_usage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dammedia',
            name='limit_usage',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]
