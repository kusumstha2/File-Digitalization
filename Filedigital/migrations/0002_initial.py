# Generated by Django 5.1.7 on 2025-04-06 07:02

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Filedigital', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='backup',
            name='uploaded_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='backup_upload', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='backup',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Filedigital.category'),
        ),
        migrations.AddField(
            model_name='file',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Filedigital.category'),
        ),
        migrations.AddField(
            model_name='file',
            name='uploaded_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='upload', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='fileactivitylog',
            name='file',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Filedigital.file'),
        ),
        migrations.AddField(
            model_name='fileactivitylog',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='fileapproval',
            name='approver',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='approver', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='fileapproval',
            name='file',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Filedigital.file'),
        ),
        migrations.AddField(
            model_name='ocrdata',
            name='file',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='Filedigital.file'),
        ),
    ]
