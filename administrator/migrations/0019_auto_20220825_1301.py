# Generated by Django 3.2.14 on 2022-08-25 13:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0018_auto_20220825_1300'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobapplied',
            name='due_date',
            field=models.DateField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='jobapplied',
            name='offer_price',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=10, null=True),
        ),
    ]