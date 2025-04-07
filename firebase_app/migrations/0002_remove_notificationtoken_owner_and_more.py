# Generated by Django 5.1.7 on 2025-04-06 07:16

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("firebase_app", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name="notificationtoken",
            name="owner",
        ),
        migrations.AddField(
            model_name="notificationtoken",
            name="user",
            field=models.ForeignKey(
                default=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="user_token",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
