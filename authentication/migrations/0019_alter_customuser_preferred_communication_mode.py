# Generated by Django 3.2.14 on 2022-08-19 10:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0018_auto_20220819_1015'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='preferred_communication_mode',
            field=models.CharField(blank=True, choices=[('0', 'Email'), ('1', 'Whatsapp'), ('2', 'Skype'), ('3', 'Direct message')], default='0', max_length=30, null=True),
        ),
    ]