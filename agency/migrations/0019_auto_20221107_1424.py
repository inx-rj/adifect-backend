# Generated by Django 3.2.14 on 2022-11-07 14:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0018_auto_20221107_1017'),
    ]

    operations = [
        migrations.AddField(
            model_name='dammedia',
            name='media_type',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='dammedia',
            name='dam',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dam_media', to='agency.dam'),
        ),
    ]
