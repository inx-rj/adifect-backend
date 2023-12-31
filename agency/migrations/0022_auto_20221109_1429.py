# Generated by Django 3.2.14 on 2022-11-09 14:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0021_dammedia_skills'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dammedia',
            name='limit_usage',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='dammedia',
            name='usage',
            field=models.IntegerField(choices=[(1, 'Public'), (0, 'Private')], default=0),
        ),
    ]
