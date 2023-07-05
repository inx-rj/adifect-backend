# Generated by Django 3.2.14 on 2023-06-26 08:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0026_audience_audience_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='StoryStatusConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_trashed', models.BooleanField(default=False)),
                ('last_page', models.IntegerField(blank=True, null=True)),
                ('is_completed', models.BooleanField(default=False)),
                ('community', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='story_status_community', to='community.community')),
            ],
            options={
                'verbose_name_plural': 'StoryStatusConfigs',
            },
        ),
    ]