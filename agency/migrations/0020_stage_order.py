# Generated by Django 3.2.14 on 2022-08-31 13:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0019_stage'),
    ]

    operations = [
        migrations.AddField(
            model_name='stage',
            name='order',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]