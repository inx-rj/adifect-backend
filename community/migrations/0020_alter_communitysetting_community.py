# Generated by Django 3.2.14 on 2023-05-03 05:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0019_creativecode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='communitysetting',
            name='community',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='community_setting_community', to='community.community'),
        ),
    ]