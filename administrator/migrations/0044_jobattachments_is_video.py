# Generated by Django 3.2.14 on 2023-01-09 12:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0043_auto_20230104_1411'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobattachments',
            name='is_video',
            field=models.BooleanField(default=False),
        ),
    ]
