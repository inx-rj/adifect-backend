# Generated by Django 3.2.14 on 2023-07-21 07:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0049_memberapprovals_comment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='memberapprovals',
            name='message',
            field=models.TextField(blank=True, default=None, null=True),
        ),
    ]
