# Generated by Django 3.2.14 on 2022-07-26 14:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0010_auto_20220726_1246'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='portfolio',
        ),
        migrations.CreateModel(
            name='CustomUserPortfolio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('portfolio_images', models.FileField(blank=True, null=True, upload_to='user_portfolio')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]