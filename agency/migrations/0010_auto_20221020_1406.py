# Generated by Django 3.2.14 on 2022-10-20 14:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0009_auto_20221019_0944'),
    ]

    operations = [
        migrations.AddField(
            model_name='dammedia',
            name='description',
            field=models.CharField(blank=True, default=None, max_length=2000, null=True),
        ),
        migrations.AddField(
            model_name='dammedia',
            name='title',
            field=models.CharField(blank=True, default=None, max_length=300, null=True),
        ),
    ]