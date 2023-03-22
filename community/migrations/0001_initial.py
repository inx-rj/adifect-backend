# Generated by Django 3.2.14 on 2023-03-22 09:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Community',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_trashed', models.BooleanField(default=False)),
                ('community_id', models.IntegerField(unique=True)),
                ('name', models.CharField(max_length=50)),
                ('client_company_id', models.IntegerField()),
                ('state', models.CharField(blank=True, max_length=50, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name_plural': 'Community',
            },
        ),
        migrations.CreateModel(
            name='Story',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_trashed', models.BooleanField(default=False)),
                ('title', models.CharField(max_length=200)),
                ('lede', models.TextField()),
                ('image', models.ImageField(blank=True, null=True, upload_to='story_image/')),
                ('word_count', models.IntegerField(default=0)),
                ('publication_date', models.DateField()),
                ('status', models.CharField(blank=True, max_length=50, null=True)),
                ('body', models.TextField()),
                ('p_url', models.CharField(max_length=8, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('community', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='story_community', to='community.community')),
            ],
            options={
                'verbose_name_plural': 'Story',
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_trashed', models.BooleanField(default=False)),
                ('title', models.CharField(max_length=200)),
                ('is_unique', models.BooleanField(default=True)),
                ('description', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('community', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tag_community', to='community.community')),
            ],
            options={
                'verbose_name_plural': 'Tag',
            },
        ),
        migrations.CreateModel(
            name='StoryTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('story', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='community.story')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='community.tag')),
            ],
        ),
        migrations.AddField(
            model_name='story',
            name='tag',
            field=models.ManyToManyField(related_name='story_tag', through='community.StoryTag', to='community.Tag'),
        ),
    ]
