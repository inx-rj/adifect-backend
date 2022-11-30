# Generated by Django 3.2.14 on 2022-11-30 12:34

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('agency', '0034_remove_agencylevel_is_test'),
    ]

    operations = [
        migrations.AddField(
            model_name='industry',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='Industry_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='workflow_stages',
            name='is_nudge',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='workflow_stages',
            name='nudge_time',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='agencylevel',
            name='levels',
            field=models.IntegerField(choices=[(1, 'Agency Admin'), (2, 'Agency Marketer'), (3, 'Agency Approver'), (4, 'Creator In House')], default=None),
        ),
    ]
