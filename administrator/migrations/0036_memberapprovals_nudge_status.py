# Generated by Django 3.2.14 on 2022-12-02 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0035_remove_jobtemplate_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='memberapprovals',
            name='nudge_status',
            field=models.CharField(blank=True, default='', max_length=50000, null=True),
        ),
    ]