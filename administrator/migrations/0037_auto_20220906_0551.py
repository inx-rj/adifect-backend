# Generated by Django 3.2.14 on 2022-09-06 05:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('administrator', '0036_auto_20220906_0545'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activities',
            name='hired_user',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.SET_DEFAULT, to='administrator.jobhired'),
        ),
        migrations.AlterField(
            model_name='activities',
            name='job_id',
            field=models.ForeignKey(db_column='job_id', default=None, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='job_id', to='administrator.job'),
        ),
        migrations.AlterField(
            model_name='activities',
            name='job_owner',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='job_owner_id', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='activities',
            name='sender',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='sender_id', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='activityattachments',
            name='activities',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='images', to='administrator.activities'),
        ),
        migrations.AlterField(
            model_name='jobapplied',
            name='job',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.SET_DEFAULT, to='administrator.job'),
        ),
        migrations.AlterField(
            model_name='jobapplied',
            name='user',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.SET_DEFAULT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='jobappliedattachments',
            name='job_applied',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='images', to='administrator.jobapplied'),
        ),
        migrations.AlterField(
            model_name='jobattachments',
            name='job',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='images', to='administrator.job'),
        ),
        migrations.AlterField(
            model_name='jobhired',
            name='job',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.SET_DEFAULT, to='administrator.job'),
        ),
        migrations.AlterField(
            model_name='preferredlanguage',
            name='user',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.SET_DEFAULT, to=settings.AUTH_USER_MODEL),
        ),
    ]
