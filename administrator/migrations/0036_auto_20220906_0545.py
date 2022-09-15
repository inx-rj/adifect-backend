# Generated by Django 3.2.14 on 2022-09-06 05:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('administrator', '0035_alter_activities_job_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='administrator.category'),
        ),
        migrations.AlterField(
            model_name='job',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='administrator.company'),
        ),
        migrations.AlterField(
            model_name='job',
            name='industry',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='administrator.industry'),
        ),
        migrations.AlterField(
            model_name='job',
            name='level',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='administrator.level'),
        ),
        migrations.AlterField(
            model_name='job',
            name='user',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.SET_DEFAULT, to=settings.AUTH_USER_MODEL),
        ),
    ]
