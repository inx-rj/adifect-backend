# Generated by Django 3.2.14 on 2022-08-25 13:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0017_auto_20220825_1259'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='jobapplied',
            name='due_date',
        ),
        migrations.RemoveField(
            model_name='jobapplied',
            name='offer_price',
        ),
    ]