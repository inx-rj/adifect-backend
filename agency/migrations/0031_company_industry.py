# Generated by Django 3.2.14 on 2022-11-22 08:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0030_dam_applied_creator'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='industry',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='company_industry', to='agency.industry'),
        ),
    ]
