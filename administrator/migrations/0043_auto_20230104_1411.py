# Generated by Django 3.2.14 on 2023-01-04 14:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('administrator', '0042_help_helpattachments'),
    ]

    operations = [
        migrations.CreateModel(
            name='HelpChat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_trashed', models.BooleanField(default=False)),
                ('chat', models.TextField(blank=True, default=None, null=True)),
                ('is_admin', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name_plural': 'Help Chat',
            },
        ),
        migrations.AlterModelOptions(
            name='help',
            options={'verbose_name_plural': 'Help'},
        ),
        migrations.AlterModelOptions(
            name='helpattachments',
            options={'verbose_name_plural': 'Help Attachments'},
        ),
        migrations.CreateModel(
            name='HelpChatAttachments',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_trashed', models.BooleanField(default=False)),
                ('chat_new_attachments', models.FileField(blank=True, default=None, null=True, upload_to='helpchat_attachments')),
                ('chat_attachments', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='chat_attachments_user', to='administrator.helpchat')),
            ],
            options={
                'verbose_name_plural': 'Help Chat Attachments',
            },
        ),
        migrations.AddField(
            model_name='helpchat',
            name='help',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='helpChat_user', to='administrator.help'),
        ),
        migrations.AddField(
            model_name='helpchat',
            name='receiver',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='receiver_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='helpchat',
            name='sender',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sender_user', to=settings.AUTH_USER_MODEL),
        ),
    ]