# Generated by Django 3.2.14 on 2022-09-09 10:34

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0065_remove_jobtemplate_template_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobtemplate',
            name='template_name',
            field=models.CharField(default=django.utils.timezone.now, max_length=250),
            preserve_default=False,
        ),
    ]