# Generated by Django 3.2.14 on 2022-11-11 10:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0027_auto_20221111_0741'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dam',
            name='type',
            field=models.IntegerField(choices=[(1, 'Folder'), (2, 'Collection'), (3, 'Image')], default=None),
        ),
    ]