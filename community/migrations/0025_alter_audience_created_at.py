# Generated by Django 3.2.14 on 2023-06-13 09:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0024_audience_community'),
    ]

    operations = [
        migrations.AlterField(
            model_name='audience',
            name='created_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]