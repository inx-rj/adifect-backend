# Generated by Django 3.2.14 on 2022-11-15 15:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0009_customuser_sub_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='Language',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='website',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]