# Generated by Django 3.2.14 on 2022-11-10 11:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0030_auto_20221110_1013'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobattachments',
            name='dam_media_id',
            field=models.CharField(blank=True, default=None, max_length=5000000, null=True),
        ),
    ]
