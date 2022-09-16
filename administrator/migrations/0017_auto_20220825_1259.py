# Generated by Django 3.2.14 on 2022-08-25 12:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0016_jobhired_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobapplied',
            name='due_date',
            field=models.DateField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='jobapplied',
            name='links',
            field=models.CharField(blank=True, default=None, max_length=50000, null=True),
        ),
        migrations.AddField(
            model_name='jobapplied',
            name='offer_price',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=10, null=True),
        ),
    ]