# Generated by Django 3.2.14 on 2022-08-30 06:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0023_alter_job_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobapplied',
            name='porposed_due_date',
            field=models.DateField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='jobapplied',
            name='porposed_price',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='jobapplied',
            name='status',
            field=models.IntegerField(choices=[(0, 'Applied'), (1, 'In Review'), (2, 'Hire')], default=0),
        ),
    ]