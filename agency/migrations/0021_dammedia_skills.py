# Generated by Django 3.2.14 on 2022-11-09 10:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0028_auto_20221109_1005'),
        ('agency', '0020_auto_20221108_1117'),
    ]

    operations = [
        migrations.AddField(
            model_name='dammedia',
            name='skills',
            field=models.ManyToManyField(blank=True, to='administrator.Skills'),
        ),
    ]
