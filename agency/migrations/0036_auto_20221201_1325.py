# Generated by Django 3.2.14 on 2022-12-01 13:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0035_auto_20221130_1234'),
    ]

    operations = [
         migrations.AddField(
            model_name='workflow_stages',
            name='approval_time',
            field=models.IntegerField(default=36),
        ),
        migrations.AddField(
            model_name='dam',
            name='company',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='agency.company'),
        )
    ]
