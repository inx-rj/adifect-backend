# Generated by Django 3.2.14 on 2022-10-07 07:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0011_auto_20221006_0742'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobapplied',
            name='status',
            field=models.IntegerField(choices=[(0, 'Applied'), (1, 'Reject'), (2, 'Hire'), (3, 'In Review'), (4, 'Completed')], default=0),
        ),
    ]