# Generated by Django 3.2.14 on 2023-02-02 07:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0042_invitemember_is_inactive'),
        ('notification', '0003_auto_20230112_1412'),
    ]

    operations = [
        migrations.AddField(
            model_name='notifications',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='company_notifications', to='agency.company'),
        ),
    ]
