# Generated by Django 3.2.14 on 2022-10-28 12:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0011_alter_agencylevel_levels'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='is_blocked',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='worksflow',
            name='is_blocked',
            field=models.BooleanField(default=False),
        ),
    ]
