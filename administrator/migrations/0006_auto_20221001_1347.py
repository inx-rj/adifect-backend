# Generated by Django 3.2.14 on 2022-10-01 13:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0005_auto_20220929_0826'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='job',
            name='related_jobs',
        ),
        migrations.AddField(
            model_name='job',
            name='related_jobs',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='administrator.job'),
        ),
    ]
