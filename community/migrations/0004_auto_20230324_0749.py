# Generated by Django 3.2.14 on 2023-03-24 07:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0003_alter_story_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='community',
            name='community_metadata',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='story',
            name='story_metadata',
            field=models.JSONField(blank=True, null=True),
        ),
    ]