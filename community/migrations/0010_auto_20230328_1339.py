# Generated by Django 3.2.14 on 2023-03-28 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0009_auto_20230328_0936'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='title',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='story',
            name='title',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='tag',
            name='title',
            field=models.TextField(),
        ),
    ]