# Generated by Django 3.2.14 on 2022-10-13 11:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0013_answer_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobapplied',
            name='job',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='job_applied', to='administrator.job'),
        ),
    ]
