# Generated by Django 3.2.14 on 2022-08-31 08:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('administrator', '0029_alter_preferredlanguage_ln_code'),
        ('agency', '0016_invitemember'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorksFlow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(default=None, max_length=200)),
                ('is_active', models.BooleanField(default=True)),
                ('agency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workflow_agency', to=settings.AUTH_USER_MODEL)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workflow_job', to='administrator.job')),
            ],
            options={
                'verbose_name': 'WorksFlow',
                'verbose_name_plural': 'WorksFlow',
            },
        ),
    ]