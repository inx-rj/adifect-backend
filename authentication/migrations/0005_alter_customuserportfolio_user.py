# Generated by Django 3.2.14 on 2022-10-21 12:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0004_auto_20221010_1201'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuserportfolio',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='Portfolio_user', to=settings.AUTH_USER_MODEL),
        ),
    ]
